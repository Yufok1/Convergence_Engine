#!/usr/bin/env python3
"""
🔗 CocoonLink - Peer-to-Peer Networking for Cocoons

This module enables cocoons to connect to CocoonHatch servers and interact
with other cocoons over the internet - battles, trades, chat, and more.

This file can be:
1. Embedded into cocoon.py during export (for standalone networking)
2. Imported by cocoon.py as a module

Usage:
    # From command line (if embedded in cocoon)
    python cocoon.py --link --hatch ws://some-hatch:9000
    
    # From Python
    from cocoon_link import CocoonLink
    link = CocoonLink(cocoon_agent)
    await link.connect("ws://localhost:9000")
    await link.challenge("Bob's Swarm")

Protocol: See cocoon_hatch.py for full protocol documentation.

Author: Convergence Engine Project
License: MIT
"""

import asyncio
import json
import logging
import time
import threading
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, TYPE_CHECKING
from queue import Queue
import sys

# Try websockets library
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class RemoteUser:
    """Info about another user on the hatch."""
    user_id: str
    display_name: str
    organism_count: int = 0
    total_fitness: float = 0.0
    battle_wins: int = 0
    battle_losses: int = 0
    vocab_size: int = 0
    status: str = "idle"
    online_duration: int = 0
    
    @property
    def win_rate(self) -> float:
        total = self.battle_wins + self.battle_losses
        return self.battle_wins / total if total > 0 else 0.0
    
    def __str__(self):
        status_icon = "⚔️" if self.status == "battling" else "🟢"
        return f"{status_icon} {self.display_name} | 🧬{self.organism_count} | 🏆{self.battle_wins}/{self.battle_losses}"


@dataclass
class BattleState:
    """Current battle state."""
    battle_id: str
    opponent: RemoteUser
    is_user1: bool
    round_number: int = 0
    started_at: float = field(default_factory=time.time)
    my_score: float = 0.0
    opponent_score: float = 0.0
    state: str = "active"  # active, won, lost, draw


@dataclass
class Challenge:
    """A pending challenge."""
    challenge_id: str
    challenger: RemoteUser
    battle_type: str
    message: str
    received_at: float = field(default_factory=time.time)


# =============================================================================
# COCOON LINK CLIENT
# =============================================================================

class CocoonLink:
    """
    Networking client for cocoons.
    
    Handles connection to CocoonHatch servers and provides
    high-level API for battles, trades, and chat.
    """
    
    def __init__(self, cocoon_agent=None, display_name: str = "Anonymous Cocoon"):
        """
        Initialize CocoonLink.
        
        Args:
            cocoon_agent: The CocoonAgent instance (for battle integration)
            display_name: Display name shown to other users
        """
        self.cocoon = cocoon_agent
        self.display_name = display_name
        
        # Connection state
        self.websocket = None
        self.connected = False
        self.user_id: Optional[str] = None
        self.hatch_url: Optional[str] = None
        
        # Remote users
        self.users: Dict[str, RemoteUser] = {}
        
        # Battle state
        self.current_battle: Optional[BattleState] = None
        self.pending_challenges: Dict[str, Challenge] = {}
        
        # Event handlers
        self.on_user_joined: Optional[Callable] = None
        self.on_user_left: Optional[Callable] = None
        self.on_challenged: Optional[Callable] = None
        self.on_battle_start: Optional[Callable] = None
        self.on_battle_msg: Optional[Callable] = None
        self.on_battle_end: Optional[Callable] = None
        self.on_chat: Optional[Callable] = None
        
        # Message queue for synchronous access
        self._msg_queue: Queue = Queue()
        
        # Background task handle
        self._receive_task = None
    
    def _get_cocoon_stats(self) -> Dict[str, Any]:
        """Extract stats from cocoon for display to others."""
        if not self.cocoon:
            return {}
        
        stats = {
            'organism_count': len(getattr(self.cocoon, 'brains', [])),
            'total_fitness': 0.0,
            'battle_wins': getattr(self.cocoon, 'battle_wins', 0),
            'battle_losses': getattr(self.cocoon, 'battle_losses', 0),
            'vocab_size': len(getattr(self.cocoon, 'vocab', {})),
        }
        
        # Calculate total fitness if available
        if hasattr(self.cocoon, 'brains'):
            for brain in self.cocoon.brains:
                if hasattr(brain, 'fitness'):
                    stats['total_fitness'] += brain.fitness
        
        return stats
    
    # -------------------------------------------------------------------------
    # CONNECTION
    # -------------------------------------------------------------------------
    
    async def connect(self, hatch_url: str = "ws://localhost:9000") -> bool:
        """
        Connect to a CocoonHatch server.
        
        Args:
            hatch_url: WebSocket URL of the hatch (e.g., "ws://localhost:9000")
        
        Returns:
            True if connected successfully
        """
        if not WEBSOCKETS_AVAILABLE:
            print("❌ websockets library not found. Install with: pip install websockets")
            return False
        
        self.hatch_url = hatch_url
        
        try:
            print(f"🔗 Connecting to {hatch_url}...")
            self.websocket = await websockets.connect(hatch_url)
            self.connected = True
            
            # Register with hatch
            await self._send('REGISTER', {
                'display_name': self.display_name,
                **self._get_cocoon_stats()
            })
            
            # Wait for registration confirmation
            response = await self._receive_one()
            if response and response.get('type') == 'REGISTERED':
                self.user_id = response['data'].get('user_id')
                online_count = response['data'].get('online_users', 0)
                print(f"✅ Connected as {self.display_name} ({self.user_id})")
                print(f"📊 {online_count} users online")
                
                # Start background receiver
                self._receive_task = asyncio.create_task(self._receive_loop())
                
                return True
            else:
                print(f"❌ Registration failed: {response}")
                return False
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the hatch."""
        if self.websocket:
            await self.websocket.close()
        self.connected = False
        self.websocket = None
        self.user_id = None
        if self._receive_task:
            self._receive_task.cancel()
        print("👋 Disconnected from hatch")
    
    # -------------------------------------------------------------------------
    # MESSAGING
    # -------------------------------------------------------------------------
    
    async def _send(self, msg_type: str, data: Dict):
        """Send a message to the hatch."""
        if not self.websocket:
            return
        message = json.dumps({'type': msg_type, 'data': data})
        await self.websocket.send(message)
    
    async def _receive_one(self) -> Optional[Dict]:
        """Receive a single message."""
        if not self.websocket:
            return None
        try:
            message = await self.websocket.recv()
            return json.loads(message)
        except Exception:
            return None
    
    async def _receive_loop(self):
        """Background loop to receive and process messages."""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError:
                    continue
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            print("⚠️ Connection to hatch lost")
        except asyncio.CancelledError:
            pass
    
    async def _handle_message(self, msg: Dict):
        """Handle incoming message from hatch."""
        msg_type = msg.get('type', '')
        data = msg.get('data', {})
        
        if msg_type == 'USER_LIST':
            self.users.clear()
            for u in data.get('users', []):
                user = RemoteUser(**u)
                if user.user_id != self.user_id:
                    self.users[user.user_id] = user
        
        elif msg_type == 'USER_JOINED':
            user_data = data.get('user', {})
            user = RemoteUser(**user_data)
            if user.user_id != self.user_id:
                self.users[user.user_id] = user
                print(f"➕ {user.display_name} joined")
                if self.on_user_joined:
                    self.on_user_joined(user)
        
        elif msg_type == 'USER_LEFT':
            user_id = data.get('user_id')
            name = data.get('display_name', 'Someone')
            if user_id in self.users:
                del self.users[user_id]
            print(f"➖ {name} left")
            if self.on_user_left:
                self.on_user_left(user_id, name)
        
        elif msg_type == 'CHALLENGED':
            challenger_data = data.get('challenger', {})
            challenger = RemoteUser(**challenger_data)
            challenge = Challenge(
                challenge_id=data.get('challenge_id'),
                challenger=challenger,
                battle_type=data.get('battle_type', 'standard'),
                message=data.get('message', '')
            )
            self.pending_challenges[challenge.challenge_id] = challenge
            print(f"\n⚔️ CHALLENGE from {challenger.display_name}!")
            if challenge.message:
                print(f"   \"{challenge.message}\"")
            print(f"   Type /accept {challenge.challenge_id[:8]} or /decline {challenge.challenge_id[:8]}")
            if self.on_challenged:
                self.on_challenged(challenge)
        
        elif msg_type == 'CHALLENGE_SENT':
            target = data.get('target', {})
            print(f"📤 Challenge sent to {target.get('display_name', 'unknown')}")
        
        elif msg_type == 'CHALLENGE_ACCEPTED':
            opponent_data = data.get('opponent', {})
            opponent = RemoteUser(**opponent_data)
            self.current_battle = BattleState(
                battle_id=data.get('battle_id'),
                opponent=opponent,
                is_user1=(data.get('you_are') == 'user1')
            )
            print(f"\n🎮 BATTLE STARTING vs {opponent.display_name}!")
            if self.on_battle_start:
                self.on_battle_start(self.current_battle)
        
        elif msg_type == 'BATTLE_START':
            opponent_data = data.get('opponent', {})
            opponent = RemoteUser(**opponent_data)
            self.current_battle = BattleState(
                battle_id=data.get('battle_id'),
                opponent=opponent,
                is_user1=(data.get('you_are') == 'user1')
            )
            print(f"\n🎮 BATTLE STARTING vs {opponent.display_name}!")
            if self.on_battle_start:
                self.on_battle_start(self.current_battle)
        
        elif msg_type == 'CHALLENGE_DECLINED':
            declined_by = data.get('declined_by', {})
            reason = data.get('reason', 'No reason given')
            print(f"❌ {declined_by.get('display_name', 'Opponent')} declined: {reason}")
        
        elif msg_type == 'BATTLE_MSG':
            if self.on_battle_msg:
                self.on_battle_msg(data)
            # Queue for synchronous processing
            self._msg_queue.put(('BATTLE_MSG', data))
        
        elif msg_type == 'BATTLE_END':
            winner_id = data.get('winner_id')
            winner_name = data.get('winner_name', 'Unknown')
            reason = data.get('reason', '')
            
            if self.current_battle:
                if winner_id == self.user_id:
                    print(f"\n🏆 YOU WON! {reason}")
                    self.current_battle.state = "won"
                elif winner_id:
                    print(f"\n💀 You lost to {winner_name}. {reason}")
                    self.current_battle.state = "lost"
                else:
                    print(f"\n🤝 Draw! {reason}")
                    self.current_battle.state = "draw"
            
            if self.on_battle_end:
                self.on_battle_end(data)
            
            self.current_battle = None
        
        elif msg_type == 'CHAT':
            sender = data.get('from', 'Unknown')
            message = data.get('message', '')
            private = data.get('private', False)
            prefix = "[PM] " if private else ""
            print(f"💬 {prefix}{sender}: {message}")
            if self.on_chat:
                self.on_chat(data)
        
        elif msg_type == 'ERROR':
            error = data.get('error', 'Unknown error')
            print(f"❌ Error: {error}")
        
        elif msg_type == 'PONG':
            pass  # Keepalive response, ignore
    
    # -------------------------------------------------------------------------
    # USER ACTIONS
    # -------------------------------------------------------------------------
    
    async def list_users(self) -> List[RemoteUser]:
        """Request and return list of online users."""
        await self._send('LIST_USERS', {})
        await asyncio.sleep(0.2)  # Give time for response
        return list(self.users.values())
    
    async def challenge(self, target: str, message: str = "") -> bool:
        """
        Challenge another user to battle.
        
        Args:
            target: Display name or user ID of target
            message: Optional trash talk / message
        
        Returns:
            True if challenge was sent
        """
        await self._send('CHALLENGE', {
            'target': target,
            'target_id': target if target.startswith('user_') else None,
            'battle_type': 'standard',
            'message': message
        })
        return True
    
    async def accept_challenge(self, challenge_id: str) -> bool:
        """Accept a pending challenge."""
        # Find full challenge ID from prefix
        full_id = None
        for cid in self.pending_challenges:
            if cid.startswith(challenge_id) or cid == challenge_id:
                full_id = cid
                break
        
        if not full_id:
            print(f"❌ Challenge not found: {challenge_id}")
            return False
        
        await self._send('ACCEPT', {'challenge_id': full_id})
        del self.pending_challenges[full_id]
        return True
    
    async def decline_challenge(self, challenge_id: str, reason: str = "Declined") -> bool:
        """Decline a pending challenge."""
        # Find full challenge ID from prefix
        full_id = None
        for cid in self.pending_challenges:
            if cid.startswith(challenge_id) or cid == challenge_id:
                full_id = cid
                break
        
        if not full_id:
            print(f"❌ Challenge not found: {challenge_id}")
            return False
        
        await self._send('DECLINE', {'challenge_id': full_id, 'reason': reason})
        del self.pending_challenges[full_id]
        return True
    
    async def send_battle_state(self, payload: Dict):
        """Send battle state to opponent."""
        if not self.current_battle:
            return
        
        self.current_battle.round_number += 1
        await self._send('BATTLE_MSG', {
            'round': self.current_battle.round_number,
            'payload': payload
        })
    
    async def end_battle(self, winner_id: Optional[str] = None, reason: str = ""):
        """End the current battle."""
        if not self.current_battle:
            return
        
        await self._send('BATTLE_END', {
            'winner_id': winner_id,
            'reason': reason
        })
    
    async def chat(self, message: str, target: Optional[str] = None):
        """Send a chat message."""
        await self._send('CHAT', {
            'message': message,
            'target': target  # None = broadcast
        })
    
    # -------------------------------------------------------------------------
    # BATTLE PROTOCOL
    # -------------------------------------------------------------------------
    
    async def run_battle(self, rounds: int = 10) -> Optional[str]:
        """
        Run a full battle against current opponent.
        
        This implements the battle protocol:
        1. Both sides send their organism's action each round
        2. Actions are compared (rock-paper-scissors style or fitness-based)
        3. Winner is determined after N rounds
        
        Returns:
            Winner's user_id, or None for draw
        """
        if not self.current_battle or not self.cocoon:
            print("❌ No active battle or cocoon")
            return None
        
        print(f"\n⚔️ Battle vs {self.current_battle.opponent.display_name}")
        print(f"   {rounds} rounds, may the fittest win!\n")
        
        my_score = 0
        opponent_score = 0
        
        for round_num in range(1, rounds + 1):
            # Get my action from cocoon
            state = self._create_battle_state(round_num)
            my_action, my_confidence = self._get_cocoon_action(state)
            
            # Send my action
            await self.send_battle_state({
                'round': round_num,
                'action': my_action,
                'confidence': my_confidence
            })
            
            # Wait for opponent's action
            opponent_action = await self._wait_for_opponent_action(timeout=30)
            if opponent_action is None:
                print("⏱️ Opponent timed out!")
                await self.end_battle(self.user_id, "Opponent timeout")
                return self.user_id
            
            # Resolve round
            round_winner = self._resolve_round(my_action, my_confidence, 
                                               opponent_action.get('action', 0),
                                               opponent_action.get('confidence', 0.5))
            
            if round_winner == 'me':
                my_score += 1
                result = "✅ You win"
            elif round_winner == 'opponent':
                opponent_score += 1
                result = "❌ Opponent wins"
            else:
                result = "🤝 Tie"
            
            action_names = ['move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate']
            my_action_name = action_names[my_action] if my_action < len(action_names) else str(my_action)
            opp_action_name = action_names[opponent_action.get('action', 0)] if opponent_action.get('action', 0) < len(action_names) else str(opponent_action.get('action', 0))
            
            print(f"Round {round_num}: {my_action_name} vs {opp_action_name} → {result} [{my_score}-{opponent_score}]")
            
            await asyncio.sleep(0.5)  # Pace the battle
        
        # Determine winner
        if my_score > opponent_score:
            winner_id = self.user_id
            print(f"\n🏆 VICTORY! {my_score}-{opponent_score}")
        elif opponent_score > my_score:
            winner_id = self.current_battle.opponent.user_id
            print(f"\n💀 DEFEAT! {my_score}-{opponent_score}")
        else:
            winner_id = None
            print(f"\n🤝 DRAW! {my_score}-{opponent_score}")
        
        await self.end_battle(winner_id, f"Final score: {my_score}-{opponent_score}")
        return winner_id
    
    def _create_battle_state(self, round_num: int) -> List[float]:
        """Create a 25D state vector for the battle (matches config.json input_dim=25)."""
        state = [0.0] * 25
        
        if self.current_battle:
            # Encode battle info into state
            state[0] = round_num / 10.0  # Round progress
            state[1] = self.current_battle.my_score / 10.0
            state[2] = self.current_battle.opponent_score / 10.0
            state[3] = self.current_battle.opponent.total_fitness
            state[4] = self.current_battle.opponent.organism_count / 10.0
            state[5] = 1.0 if self.current_battle.is_user1 else 0.0
            
            # Some randomness for exploration (features 6-24)
            import random
            for i in range(6, 25):
                state[i] = random.random() * 0.5
        
        return state
    
    def _get_cocoon_action(self, state: List[float]) -> tuple:
        """Get action from cocoon's neural network."""
        if not self.cocoon:
            import random
            return random.randint(0, 5), 0.5
        
        # Try to use cocoon's act method
        if hasattr(self.cocoon, 'act'):
            result = self.cocoon.act(state)
            if isinstance(result, tuple):
                return result[0], result[1] if len(result) > 1 else 0.5
            return result, 0.5
        
        # Fallback: random action
        import random
        return random.randint(0, 5), 0.5
    
    async def _wait_for_opponent_action(self, timeout: float = 30) -> Optional[Dict]:
        """Wait for opponent's battle message."""
        start = time.time()
        while time.time() - start < timeout:
            try:
                msg_type, data = self._msg_queue.get_nowait()
                if msg_type == 'BATTLE_MSG':
                    return data.get('payload', {})
            except:
                pass
            await asyncio.sleep(0.1)
        return None
    
    def _resolve_round(self, my_action: int, my_conf: float, 
                       opp_action: int, opp_conf: float) -> str:
        """
        Resolve a battle round.
        
        Simple rules:
        - compete beats rest, reproduce, isolate
        - cooperate beats compete (cooperation stronger than aggression)
        - move beats cooperate (mobility defeats cooperation)
        - rest beats move (patience defeats mobility)
        - On same action: higher confidence wins
        """
        # Action hierarchy (circular dominance)
        # 0:move > 1:cooperate > 2:compete > 3:rest > 4:reproduce > 5:isolate > 0:move
        
        if my_action == opp_action:
            # Same action: confidence decides
            if my_conf > opp_conf + 0.1:
                return 'me'
            elif opp_conf > my_conf + 0.1:
                return 'opponent'
            return 'tie'
        
        # Circular dominance (each action beats the next 2)
        my_wins = (opp_action - my_action) % 6 in [1, 2]
        opp_wins = (my_action - opp_action) % 6 in [1, 2]
        
        if my_wins and not opp_wins:
            return 'me'
        elif opp_wins and not my_wins:
            return 'opponent'
        
        # Confidence tiebreaker
        if my_conf > opp_conf:
            return 'me'
        elif opp_conf > my_conf:
            return 'opponent'
        return 'tie'


# =============================================================================
# INTERACTIVE CLI
# =============================================================================

async def interactive_link(cocoon_agent=None, display_name: str = "Anonymous", 
                          hatch_url: str = "ws://localhost:9000"):
    """
    Run interactive link mode.
    
    Commands:
        /users          - List online users
        /challenge NAME - Challenge a user
        /accept ID      - Accept a challenge
        /decline ID     - Decline a challenge
        /chat MESSAGE   - Send to lobby
        /pm NAME MSG    - Private message
        /quit           - Disconnect
    """
    link = CocoonLink(cocoon_agent, display_name)
    
    if not await link.connect(hatch_url):
        return
    
    print("\n📖 Commands: /users /challenge /accept /decline /chat /pm /quit")
    print("=" * 60)
    
    # Auto-battle handler
    async def on_battle_start(battle: BattleState):
        print("\n🎮 Starting automated battle...")
        await link.run_battle(rounds=10)
    
    link.on_battle_start = on_battle_start
    
    # Input loop
    while link.connected:
        try:
            # Non-blocking input check
            await asyncio.sleep(0.1)
            
            # Check for user input (this is tricky in async, simplified here)
            # In a real app, you'd use aioconsole or similar
            import sys
            import select
            
            # Simple blocking input for now
            if sys.platform != 'win32':
                # Unix: use select
                if select.select([sys.stdin], [], [], 0)[0]:
                    line = sys.stdin.readline().strip()
                    await process_command(link, line)
            else:
                # Windows: use thread-based input
                # For simplicity, just use blocking input with timeout simulation
                pass
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.debug(f"Input error: {e}")
    
    await link.disconnect()


async def process_command(link: CocoonLink, line: str):
    """Process a user command."""
    if not line:
        return
    
    parts = line.split(maxsplit=2)
    cmd = parts[0].lower()
    
    if cmd == '/users':
        users = await link.list_users()
        if users:
            print("\n👥 Online Users:")
            for u in users:
                print(f"   {u}")
        else:
            print("No other users online")
    
    elif cmd == '/challenge' and len(parts) > 1:
        target = parts[1]
        message = parts[2] if len(parts) > 2 else ""
        await link.challenge(target, message)
    
    elif cmd == '/accept' and len(parts) > 1:
        await link.accept_challenge(parts[1])
    
    elif cmd == '/decline' and len(parts) > 1:
        reason = parts[2] if len(parts) > 2 else "Declined"
        await link.decline_challenge(parts[1], reason)
    
    elif cmd == '/chat' and len(parts) > 1:
        message = ' '.join(parts[1:])
        await link.chat(message)
    
    elif cmd == '/pm' and len(parts) > 2:
        target = parts[1]
        message = parts[2]
        # Find user ID by name
        for uid, user in link.users.items():
            if user.display_name.lower() == target.lower():
                await link.chat(message, uid)
                break
        else:
            print(f"User not found: {target}")
    
    elif cmd == '/quit':
        await link.disconnect()
    
    else:
        print("Unknown command. Try: /users /challenge /accept /decline /chat /pm /quit")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run standalone link mode for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="🔗 CocoonLink - Connect to the network")
    parser.add_argument('--hatch', default='ws://localhost:9000', help='Hatch URL')
    parser.add_argument('--name', default='TestCocoon', help='Display name')
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    🔗 COCOON LINK                            ║
╠══════════════════════════════════════════════════════════════╣
║  Connecting to: {args.hatch:<43} ║
║  Display name:  {args.name:<43} ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(interactive_link(None, args.name, args.hatch))


if __name__ == "__main__":
    main()
