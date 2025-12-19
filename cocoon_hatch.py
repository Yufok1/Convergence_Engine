#!/usr/bin/env python3
"""
🥚 CocoonHatch - Decentralized Relay Server for Cocoon Battles

A lightweight WebSocket server that anyone can host to enable cocoon-to-cocoon
battles, trades, and interactions over the internet.

Usage:
    python cocoon_hatch.py                    # Start on default port 9000
    python cocoon_hatch.py --port 8080        # Custom port
    python cocoon_hatch.py --public           # Bind to 0.0.0.0 (accessible from internet)

Cocoons connect with:
    python cocoon.py --link --hatch ws://your-server:9000

Protocol:
    All messages are JSON with {"type": "...", "data": {...}}
    
    Client -> Server:
        REGISTER    - Join hatch with display name and cocoon stats
        CHALLENGE   - Challenge another user to battle
        ACCEPT      - Accept a challenge
        DECLINE     - Decline a challenge
        BATTLE_MSG  - Forward battle state to opponent
        CHAT        - Send chat message to lobby or opponent
        LIST_USERS  - Request online user list
        DISCONNECT  - Graceful disconnect
    
    Server -> Client:
        REGISTERED  - Confirmation with your user ID
        USER_LIST   - List of online users
        USER_JOINED - Someone came online
        USER_LEFT   - Someone went offline
        CHALLENGED  - You received a challenge
        CHALLENGE_ACCEPTED - Your challenge was accepted
        CHALLENGE_DECLINED - Your challenge was declined
        BATTLE_START - Battle is beginning
        BATTLE_MSG  - Forwarded battle state from opponent
        BATTLE_END  - Battle concluded
        CHAT        - Chat message from someone
        ERROR       - Error message

Author: Convergence Engine Project
License: MIT
"""

import asyncio
import json
import argparse
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, Set, Any, List
from datetime import datetime

# Try websockets library
try:
    import websockets
    from websockets.server import serve
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("❌ websockets library not found. Install with: pip install websockets")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class CocoonUser:
    """A connected cocoon user."""
    user_id: str
    display_name: str
    websocket: Any  # websockets.WebSocketServerProtocol
    connected_at: float = field(default_factory=time.time)
    
    # Cocoon stats (for matchmaking display)
    organism_count: int = 0
    total_fitness: float = 0.0
    battle_wins: int = 0
    battle_losses: int = 0
    vocab_size: int = 0
    
    # State
    status: str = "idle"  # idle, battling, away
    current_opponent: Optional[str] = None
    current_battle_id: Optional[str] = None
    
    def to_public_dict(self) -> Dict[str, Any]:
        """Public info visible to other users."""
        return {
            'user_id': self.user_id,
            'display_name': self.display_name,
            'organism_count': self.organism_count,
            'total_fitness': round(self.total_fitness, 3),
            'battle_wins': self.battle_wins,
            'battle_losses': self.battle_losses,
            'vocab_size': self.vocab_size,
            'status': self.status,
            'online_duration': int(time.time() - self.connected_at)
        }


@dataclass
class Battle:
    """An active battle between two users."""
    battle_id: str
    user1_id: str
    user2_id: str
    started_at: float = field(default_factory=time.time)
    round_number: int = 0
    state: str = "in_progress"  # in_progress, completed, abandoned
    winner_id: Optional[str] = None
    
    # Battle log
    messages: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PendingChallenge:
    """A challenge waiting for response."""
    challenge_id: str
    challenger_id: str
    challenged_id: str
    created_at: float = field(default_factory=time.time)
    battle_type: str = "standard"  # standard, ranked, friendly
    message: str = ""


# =============================================================================
# COCOON HATCH SERVER
# =============================================================================

class CocoonHatch:
    """
    The relay server that connects cocoons together.
    
    Handles:
    - User registration and presence
    - Challenge/accept flow
    - Battle message forwarding
    - Chat relay
    """
    
    def __init__(self, host: str = "localhost", port: int = 9000):
        self.host = host
        self.port = port
        
        # Connected users: user_id -> CocoonUser
        self.users: Dict[str, CocoonUser] = {}
        
        # WebSocket -> user_id mapping for quick lookup
        self.ws_to_user: Dict[Any, str] = {}
        
        # Active battles: battle_id -> Battle
        self.battles: Dict[str, Battle] = {}
        
        # Pending challenges: challenge_id -> PendingChallenge
        self.pending_challenges: Dict[str, PendingChallenge] = {}
        
        # Stats
        self.total_connections = 0
        self.total_battles = 0
        self.started_at = time.time()
        
        logger.info(f"🥚 CocoonHatch initialized on {host}:{port}")
    
    # -------------------------------------------------------------------------
    # MESSAGE HANDLERS
    # -------------------------------------------------------------------------
    
    async def handle_message(self, websocket, message: str):
        """Route incoming message to appropriate handler."""
        try:
            data = json.loads(message)
            msg_type = data.get('type', '').upper()
            payload = data.get('data', {})
            
            handlers = {
                'REGISTER': self.handle_register,
                'LIST_USERS': self.handle_list_users,
                'CHALLENGE': self.handle_challenge,
                'ACCEPT': self.handle_accept,
                'DECLINE': self.handle_decline,
                'BATTLE_MSG': self.handle_battle_msg,
                'BATTLE_END': self.handle_battle_end,
                'CHAT': self.handle_chat,
                'PING': self.handle_ping,
            }
            
            handler = handlers.get(msg_type)
            if handler:
                await handler(websocket, payload)
            else:
                await self.send_error(websocket, f"Unknown message type: {msg_type}")
                
        except json.JSONDecodeError:
            await self.send_error(websocket, "Invalid JSON")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_error(websocket, str(e))
    
    async def handle_register(self, websocket, data: Dict):
        """Register a new cocoon user."""
        display_name = data.get('display_name', 'Anonymous')[:32]
        
        # Generate unique ID
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        
        # Create user
        user = CocoonUser(
            user_id=user_id,
            display_name=display_name,
            websocket=websocket,
            organism_count=data.get('organism_count', 0),
            total_fitness=data.get('total_fitness', 0.0),
            battle_wins=data.get('battle_wins', 0),
            battle_losses=data.get('battle_losses', 0),
            vocab_size=data.get('vocab_size', 0),
        )
        
        self.users[user_id] = user
        self.ws_to_user[websocket] = user_id
        self.total_connections += 1
        
        logger.info(f"✅ {display_name} ({user_id}) joined the hatch")
        
        # Send confirmation
        await self.send(websocket, 'REGISTERED', {
            'user_id': user_id,
            'display_name': display_name,
            'server_time': time.time(),
            'online_users': len(self.users)
        })
        
        # Notify others
        await self.broadcast('USER_JOINED', {
            'user': user.to_public_dict()
        }, exclude={user_id})
        
        # Send current user list
        await self.handle_list_users(websocket, {})
    
    async def handle_list_users(self, websocket, data: Dict):
        """Send list of online users."""
        users = [u.to_public_dict() for u in self.users.values()]
        await self.send(websocket, 'USER_LIST', {
            'users': users,
            'count': len(users)
        })
    
    async def handle_challenge(self, websocket, data: Dict):
        """Send a battle challenge to another user."""
        challenger_id = self.ws_to_user.get(websocket)
        if not challenger_id:
            await self.send_error(websocket, "Not registered")
            return
        
        target_name = data.get('target')
        target_id = data.get('target_id')
        battle_type = data.get('battle_type', 'standard')
        message = data.get('message', '')[:200]
        
        # Find target by name or ID
        target_user = None
        if target_id and target_id in self.users:
            target_user = self.users[target_id]
        elif target_name:
            for u in self.users.values():
                if u.display_name.lower() == target_name.lower():
                    target_user = u
                    break
        
        if not target_user:
            await self.send_error(websocket, f"User not found: {target_name or target_id}")
            return
        
        if target_user.user_id == challenger_id:
            await self.send_error(websocket, "Cannot challenge yourself!")
            return
        
        if target_user.status == "battling":
            await self.send_error(websocket, f"{target_user.display_name} is already in a battle")
            return
        
        # Create challenge
        challenge_id = f"chal_{uuid.uuid4().hex[:8]}"
        challenge = PendingChallenge(
            challenge_id=challenge_id,
            challenger_id=challenger_id,
            challenged_id=target_user.user_id,
            battle_type=battle_type,
            message=message
        )
        self.pending_challenges[challenge_id] = challenge
        
        challenger = self.users[challenger_id]
        
        logger.info(f"⚔️ {challenger.display_name} challenged {target_user.display_name}")
        
        # Notify the challenged user
        await self.send(target_user.websocket, 'CHALLENGED', {
            'challenge_id': challenge_id,
            'challenger': challenger.to_public_dict(),
            'battle_type': battle_type,
            'message': message
        })
        
        # Confirm to challenger
        await self.send(websocket, 'CHALLENGE_SENT', {
            'challenge_id': challenge_id,
            'target': target_user.to_public_dict()
        })
    
    async def handle_accept(self, websocket, data: Dict):
        """Accept a battle challenge."""
        user_id = self.ws_to_user.get(websocket)
        challenge_id = data.get('challenge_id')
        
        if not challenge_id or challenge_id not in self.pending_challenges:
            await self.send_error(websocket, "Challenge not found or expired")
            return
        
        challenge = self.pending_challenges[challenge_id]
        
        if challenge.challenged_id != user_id:
            await self.send_error(websocket, "This challenge is not for you")
            return
        
        # Create battle
        battle_id = f"battle_{uuid.uuid4().hex[:8]}"
        battle = Battle(
            battle_id=battle_id,
            user1_id=challenge.challenger_id,
            user2_id=challenge.challenged_id
        )
        self.battles[battle_id] = battle
        self.total_battles += 1
        
        # Update user states
        user1 = self.users.get(challenge.challenger_id)
        user2 = self.users.get(challenge.challenged_id)
        
        if user1:
            user1.status = "battling"
            user1.current_opponent = user2.user_id if user2 else None
            user1.current_battle_id = battle_id
        
        if user2:
            user2.status = "battling"
            user2.current_opponent = user1.user_id if user1 else None
            user2.current_battle_id = battle_id
        
        # Remove pending challenge
        del self.pending_challenges[challenge_id]
        
        logger.info(f"🎮 Battle started: {battle_id}")
        
        # Notify both users
        battle_info = {
            'battle_id': battle_id,
            'opponent': user1.to_public_dict() if user1 else None,
            'you_are': 'user2'
        }
        await self.send(websocket, 'BATTLE_START', battle_info)
        
        if user1:
            battle_info['opponent'] = user2.to_public_dict() if user2 else None
            battle_info['you_are'] = 'user1'
            await self.send(user1.websocket, 'CHALLENGE_ACCEPTED', battle_info)
    
    async def handle_decline(self, websocket, data: Dict):
        """Decline a battle challenge."""
        user_id = self.ws_to_user.get(websocket)
        challenge_id = data.get('challenge_id')
        reason = data.get('reason', 'Declined')[:100]
        
        if not challenge_id or challenge_id not in self.pending_challenges:
            await self.send_error(websocket, "Challenge not found")
            return
        
        challenge = self.pending_challenges[challenge_id]
        
        if challenge.challenged_id != user_id:
            await self.send_error(websocket, "This challenge is not for you")
            return
        
        # Notify challenger
        challenger = self.users.get(challenge.challenger_id)
        decliner = self.users.get(user_id)
        
        if challenger:
            await self.send(challenger.websocket, 'CHALLENGE_DECLINED', {
                'challenge_id': challenge_id,
                'declined_by': decliner.to_public_dict() if decliner else None,
                'reason': reason
            })
        
        # Remove challenge
        del self.pending_challenges[challenge_id]
        
        logger.info(f"❌ Challenge {challenge_id} declined")
    
    async def handle_battle_msg(self, websocket, data: Dict):
        """Forward battle state to opponent."""
        user_id = self.ws_to_user.get(websocket)
        if not user_id:
            return
        
        user = self.users.get(user_id)
        if not user or not user.current_battle_id:
            await self.send_error(websocket, "Not in a battle")
            return
        
        battle = self.battles.get(user.current_battle_id)
        if not battle:
            await self.send_error(websocket, "Battle not found")
            return
        
        # Find opponent
        opponent_id = user.current_opponent
        opponent = self.users.get(opponent_id) if opponent_id else None
        
        if not opponent:
            await self.send_error(websocket, "Opponent disconnected")
            return
        
        # Log message
        battle.messages.append({
            'from': user_id,
            'time': time.time(),
            'data': data.get('payload', {})
        })
        battle.round_number = data.get('round', battle.round_number)
        
        # Forward to opponent
        await self.send(opponent.websocket, 'BATTLE_MSG', {
            'battle_id': battle.battle_id,
            'from': user.display_name,
            'round': battle.round_number,
            'payload': data.get('payload', {})
        })
    
    async def handle_battle_end(self, websocket, data: Dict):
        """End a battle and report results."""
        user_id = self.ws_to_user.get(websocket)
        if not user_id:
            return
        
        user = self.users.get(user_id)
        if not user or not user.current_battle_id:
            return
        
        battle = self.battles.get(user.current_battle_id)
        if not battle:
            return
        
        winner_id = data.get('winner_id')
        reason = data.get('reason', 'Battle concluded')
        
        battle.state = "completed"
        battle.winner_id = winner_id
        
        # Get both users
        user1 = self.users.get(battle.user1_id)
        user2 = self.users.get(battle.user2_id)
        
        # Update stats
        if winner_id:
            winner = self.users.get(winner_id)
            loser_id = battle.user2_id if winner_id == battle.user1_id else battle.user1_id
            loser = self.users.get(loser_id)
            
            if winner:
                winner.battle_wins += 1
            if loser:
                loser.battle_losses += 1
        
        # Reset states
        for u in [user1, user2]:
            if u:
                u.status = "idle"
                u.current_opponent = None
                u.current_battle_id = None
        
        # Notify both users
        result = {
            'battle_id': battle.battle_id,
            'winner_id': winner_id,
            'winner_name': self.users[winner_id].display_name if winner_id and winner_id in self.users else None,
            'reason': reason,
            'rounds': battle.round_number,
            'duration': time.time() - battle.started_at
        }
        
        if user1:
            await self.send(user1.websocket, 'BATTLE_END', result)
        if user2:
            await self.send(user2.websocket, 'BATTLE_END', result)
        
        logger.info(f"🏁 Battle {battle.battle_id} ended - Winner: {result['winner_name'] or 'Draw'}")
    
    async def handle_chat(self, websocket, data: Dict):
        """Relay chat message."""
        user_id = self.ws_to_user.get(websocket)
        if not user_id:
            return
        
        user = self.users.get(user_id)
        if not user:
            return
        
        message = data.get('message', '')[:500]
        target = data.get('target')  # None = broadcast to lobby
        
        chat_msg = {
            'from': user.display_name,
            'from_id': user_id,
            'message': message,
            'time': time.time()
        }
        
        if target:
            # Private message
            target_user = self.users.get(target)
            if target_user:
                chat_msg['private'] = True
                await self.send(target_user.websocket, 'CHAT', chat_msg)
                await self.send(websocket, 'CHAT', chat_msg)  # Echo back
        else:
            # Lobby broadcast
            await self.broadcast('CHAT', chat_msg)
    
    async def handle_ping(self, websocket, data: Dict):
        """Respond to keepalive ping."""
        await self.send(websocket, 'PONG', {'time': time.time()})
    
    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------
    
    async def send(self, websocket, msg_type: str, data: Dict):
        """Send a message to a websocket."""
        try:
            message = json.dumps({'type': msg_type, 'data': data})
            await websocket.send(message)
        except Exception as e:
            logger.warning(f"Failed to send message: {e}")
    
    async def send_error(self, websocket, error: str):
        """Send an error message."""
        await self.send(websocket, 'ERROR', {'error': error})
    
    async def broadcast(self, msg_type: str, data: Dict, exclude: Set[str] = None):
        """Broadcast message to all connected users."""
        exclude = exclude or set()
        for user_id, user in self.users.items():
            if user_id not in exclude:
                await self.send(user.websocket, msg_type, data)
    
    async def handle_disconnect(self, websocket):
        """Clean up when a user disconnects."""
        user_id = self.ws_to_user.get(websocket)
        if not user_id:
            return
        
        user = self.users.get(user_id)
        if user:
            logger.info(f"👋 {user.display_name} ({user_id}) disconnected")
            
            # If in battle, notify opponent
            if user.current_battle_id:
                battle = self.battles.get(user.current_battle_id)
                if battle:
                    opponent_id = user.current_opponent
                    opponent = self.users.get(opponent_id) if opponent_id else None
                    if opponent:
                        await self.send(opponent.websocket, 'BATTLE_END', {
                            'battle_id': battle.battle_id,
                            'winner_id': opponent_id,
                            'reason': f"{user.display_name} disconnected",
                            'forfeit': True
                        })
                        opponent.status = "idle"
                        opponent.current_opponent = None
                        opponent.current_battle_id = None
                        opponent.battle_wins += 1
                    
                    battle.state = "abandoned"
                    battle.winner_id = opponent_id
            
            # Notify others
            await self.broadcast('USER_LEFT', {
                'user_id': user_id,
                'display_name': user.display_name
            }, exclude={user_id})
        
        # Clean up
        del self.ws_to_user[websocket]
        if user_id in self.users:
            del self.users[user_id]
        
        # Clean up any pending challenges
        to_remove = []
        for cid, challenge in self.pending_challenges.items():
            if challenge.challenger_id == user_id or challenge.challenged_id == user_id:
                to_remove.append(cid)
        for cid in to_remove:
            del self.pending_challenges[cid]
    
    # -------------------------------------------------------------------------
    # MAIN SERVER
    # -------------------------------------------------------------------------
    
    async def handle_connection(self, websocket):
        """Handle a new WebSocket connection."""
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.handle_disconnect(websocket)
    
    async def run(self):
        """Start the hatch server."""
        if not WEBSOCKETS_AVAILABLE:
            print("❌ Cannot start hatch: websockets library not installed")
            print("   Install with: pip install websockets")
            return
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    🥚  COCOON HATCH                          ║
╠══════════════════════════════════════════════════════════════╣
║  Status:  🟢 ONLINE                                          ║
║  Address: ws://{self.host}:{self.port:<5}                              ║
╠══════════════════════════════════════════════════════════════╣
║  Cocoons connect with:                                       ║
║    python cocoon.py --link --hatch ws://{self.host}:{self.port:<5}     ║
║                                                              ║
║  For internet access, use --public flag and your public IP   ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        async with serve(self.handle_connection, self.host, self.port):
            await asyncio.Future()  # Run forever


# =============================================================================
# CLI
# =============================================================================

def spawn_asset(cocoon_path: str, asset_type: str, output_dir: str = "."):
    """
    Extract/compile assets from a cocoon file.
    
    Asset types:
        readme   - Extract embedded README
        adapter  - Extract TMRL adapter (if embedded)
        onnx     - Compile brain(s) to ONNX format
        weights  - Export raw PyTorch state dicts
        vocab    - Export vocabulary JSON
        all      - Extract everything
    """
    import os
    import sys
    import importlib.util
    
    print(f"🥚 COCOON HATCH - Asset Spawner")
    print("=" * 50)
    print()
    
    if not os.path.exists(cocoon_path):
        print(f"❌ Cocoon not found: {cocoon_path}")
        return False
    
    # Load the cocoon module
    print(f"⏳ Loading cocoon: {cocoon_path}")
    try:
        spec = importlib.util.spec_from_file_location("cocoon_spawn", cocoon_path)
        cocoon_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cocoon_module)
    except Exception as e:
        print(f"❌ Failed to load cocoon: {e}")
        return False
    
    print(f"✅ Cocoon loaded")
    
    os.makedirs(output_dir, exist_ok=True)
    spawned = []
    
    # README
    if asset_type in ('readme', 'all'):
        if hasattr(cocoon_module, '_README_B64') and cocoon_module._README_B64:
            import base64
            try:
                readme_text = base64.b64decode(cocoon_module._README_B64).decode('utf-8', errors='ignore')
                readme_path = os.path.join(output_dir, "README.md")
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(readme_text)
                print(f"   📄 Spawned: {readme_path}")
                spawned.append(readme_path)
            except Exception as e:
                print(f"   ⚠️ README extraction failed: {e}")
        elif asset_type == 'readme':
            print("   ⚠️ No README embedded in this cocoon")
    
    # TMRL Adapter (if embedded)
    if asset_type in ('adapter', 'all'):
        if hasattr(cocoon_module, '_TMRL_ADAPTER_B64') and cocoon_module._TMRL_ADAPTER_B64:
            import base64
            try:
                adapter_code = base64.b64decode(cocoon_module._TMRL_ADAPTER_B64).decode('utf-8')
                adapter_path = os.path.join(output_dir, "cocoon_tmrl_adapter.py")
                with open(adapter_path, 'w', encoding='utf-8') as f:
                    f.write(adapter_code)
                print(f"   🏎️ Spawned: {adapter_path}")
                spawned.append(adapter_path)
            except Exception as e:
                print(f"   ⚠️ Adapter extraction failed: {e}")
        elif asset_type == 'adapter':
            print("   ⚠️ No TMRL adapter embedded in this cocoon")
            print("      Copy from: Convergence_Engine/cocoon_tmrl_adapter.py")
    
    # Vocabulary JSON
    if asset_type in ('vocab', 'all'):
        if hasattr(cocoon_module, '_VOCABULARY_B64') and cocoon_module._VOCABULARY_B64:
            import base64
            import zlib
            try:
                compressed = hasattr(cocoon_module, '_DATA_COMPRESSED') and cocoon_module._DATA_COMPRESSED
                raw = base64.b64decode(cocoon_module._VOCABULARY_B64)
                if compressed:
                    raw = zlib.decompress(raw)
                vocab_path = os.path.join(output_dir, "vocabulary.json")
                with open(vocab_path, 'wb') as f:
                    f.write(raw)
                print(f"   📚 Spawned: {vocab_path}")
                spawned.append(vocab_path)
            except Exception as e:
                print(f"   ⚠️ Vocabulary extraction failed: {e}")
    
    # ONNX export (single ensemble file)
    if asset_type in ('onnx', 'all'):
        if hasattr(cocoon_module, 'CocoonAgent'):
            try:
                import torch
                import torch.nn as nn
                print("   ⏳ Instantiating CocoonAgent for ONNX export...")
                agent = cocoon_module.CocoonAgent()
                
                # Create unified ensemble wrapper that handles tuple outputs
                class EnsembleWrapper(nn.Module):
                    def __init__(self, brains):
                        super().__init__()
                        self.brains = nn.ModuleList(brains)
                        self.n_brains = len(brains)
                    
                    def forward(self, x):
                        # Run all brains and average outputs
                        outputs = []
                        for brain in self.brains:
                            out = brain(x)
                            # Handle tuple returns (action, extras)
                            if isinstance(out, tuple):
                                out = out[0]
                            outputs.append(out)
                        # Stack and mean across ensemble
                        stacked = torch.stack(outputs, dim=0)  # [n_brains, batch, output_dim]
                        return stacked.mean(dim=0)  # [batch, output_dim]
                
                ensemble = EnsembleWrapper(agent.brains)
                ensemble.eval()
                
                # Determine input size from first brain
                input_dim = agent.brains[0].input_dim if hasattr(agent.brains[0], 'input_dim') else 256
                dummy_input = torch.randn(1, input_dim, device=agent.device)
                
                # Test forward pass first
                with torch.no_grad():
                    test_out = ensemble(dummy_input)
                
                onnx_path = os.path.join(output_dir, "ensemble.onnx")
                torch.onnx.export(
                    ensemble.cpu(),
                    dummy_input.cpu(),
                    onnx_path,
                    input_names=['observation'],
                    output_names=['action'],
                    dynamic_axes={
                        'observation': {0: 'batch_size'},
                        'action': {0: 'batch_size'}
                    },
                    opset_version=14
                )
                print(f"   🧬 Spawned: {onnx_path} ({len(agent.brains)} brains unified)")
                spawned.append(onnx_path)
            except Exception as e:
                print(f"   ⚠️ ONNX export failed: {e}")
    
    # Weights (single combined state dict)
    if asset_type in ('weights', 'all'):
        if hasattr(cocoon_module, 'CocoonAgent'):
            try:
                import torch
                print("   ⏳ Extracting brain weights...")
                agent = cocoon_module.CocoonAgent()
                
                # Bundle all brains into one file
                bundle = {
                    'n_brains': len(agent.brains),
                    'brains': [brain.state_dict() for brain in agent.brains],
                    'config': {
                        'input_dim': getattr(agent.brains[0], 'input_dim', None),
                        'hidden_dim': getattr(agent.brains[0], 'hidden_dim', None),
                        'output_dim': getattr(agent.brains[0], 'output_dim', None),
                    }
                }
                weights_path = os.path.join(output_dir, "ensemble_weights.pt")
                torch.save(bundle, weights_path)
                print(f"   🧠 Spawned: {weights_path} ({len(agent.brains)} brains bundled)")
                spawned.append(weights_path)
            except Exception as e:
                print(f"   ⚠️ Weights extraction failed: {e}")
    
    print()
    if spawned:
        print(f"✅ Spawned {len(spawned)} asset(s) to: {output_dir}")
    else:
        print(f"⚠️ No assets spawned for type '{asset_type}'")
    
    return len(spawned) > 0


def main():
    parser = argparse.ArgumentParser(
        description="🥚 CocoonHatch - Relay server + Asset spawner for cocoons",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
RELAY SERVER:
  python cocoon_hatch.py                    Start on localhost:9000
  python cocoon_hatch.py --port 8080        Custom port
  python cocoon_hatch.py --public           Accessible from internet

ASSET SPAWNER:
  python cocoon_hatch.py --spawn <cocoon.py> --asset readme
  python cocoon_hatch.py --spawn <cocoon.py> --asset onnx --output ./exports/
  python cocoon_hatch.py --spawn <cocoon.py> --asset all

ULTIMATE UNPACK (convenience):
    python cocoon_hatch.py --unpack <cocoon.py> --output ./ultimate_package/

Asset types: readme, adapter, vocab, onnx, weights, all
        """
    )
    
    # Relay server options
    parser.add_argument('--port', '-p', type=int, default=9000,
                        help='Port to listen on (default: 9000)')
    parser.add_argument('--public', action='store_true',
                        help='Bind to 0.0.0.0 (accessible from internet)')
    parser.add_argument('--host', type=str, default=None,
                        help='Specific host to bind to')
    
    # Asset spawner options
    parser.add_argument('--spawn', type=str, metavar='COCOON',
                        help='Path to cocoon.py file to extract assets from')
    parser.add_argument('--unpack', type=str, metavar='COCOON',
                        help='Convenience alias for --spawn <cocoon.py> --asset all (unpacks the full package)')
    parser.add_argument('--asset', type=str, default='all',
                        choices=['readme', 'adapter', 'vocab', 'onnx', 'weights', 'all'],
                        help='Asset type to spawn (default: all)')
    parser.add_argument('--output', '-o', type=str, default='.',
                        help='Output directory for spawned assets (default: current dir)')
    
    args = parser.parse_args()
    
    # Asset spawner mode
    spawn_path = args.spawn or args.unpack
    if spawn_path:
        asset_type = 'all' if args.unpack else args.asset
        success = spawn_asset(spawn_path, asset_type, args.output)
        return 0 if success else 1
    
    # Relay server mode
    # Determine host
    if args.host:
        host = args.host
    elif args.public:
        host = "0.0.0.0"
    else:
        host = "localhost"
    
    # Create and run hatch
    hatch = CocoonHatch(host=host, port=args.port)
    
    try:
        asyncio.run(hatch.run())
    except KeyboardInterrupt:
        print("\n👋 CocoonHatch shutting down...")


if __name__ == "__main__":
    main()
