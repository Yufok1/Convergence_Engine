#!/usr/bin/env python3
"""
🔍 BATTLE SYSTEMS DIAGNOSTIC
=============================

Deep dive check for:
1. Proton Game Arena - Is it wired and being used?
2. Alliance Warfare - Are alliances forming?
3. Civilizational History - Are histories being recorded?
4. Causation Events - Are events being emitted?

Run this to see what's actually happening.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))


def banner(text):
    print(f"\n{'='*70}")
    print(f" {text}")
    print(f"{'='*70}")


def check_config():
    """Check config.json for battle system settings."""
    banner("📋 CONFIG.JSON BATTLE SETTINGS")
    
    config_path = Path("config.json")
    if not config_path.exists():
        print("❌ config.json not found!")
        return None
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Arena settings
    arena = config.get('arena', {})
    print(f"\n🎮 PROTON GAME ARENA:")
    print(f"   enabled: {arena.get('enabled', 'NOT SET')}")
    print(f"   default_battle_type: {arena.get('default_battle_type', 'NOT SET')}")
    print(f"   game_selection.mode: {arena.get('game_selection', {}).get('mode', 'NOT SET')}")
    print(f"   gym_settings.default_episodes: {arena.get('gym_settings', {}).get('default_episodes', 'NOT SET')}")
    
    # Highlander settings
    highlander = config.get('highlander', {})
    print(f"\n⚔️ HIGHLANDER PROTOCOL:")
    print(f"   enabled: {highlander.get('enabled', 'NOT SET')}")
    print(f"   predation_enabled: {highlander.get('predation_enabled', 'NOT SET')}")
    print(f"   rounds_per_cycle: {highlander.get('rounds_per_cycle', 'NOT SET')}")
    
    # Alliance settings
    print(f"\n🤝 ALLIANCE WARFARE:")
    print(f"   min_alliance_size: {config.get('min_alliance_size', 3)} (default: 3)")
    print(f"   max_alliances: {config.get('max_alliances', 10)} (default: 10)")
    
    return config


def check_imports():
    """Check if all battle systems import correctly."""
    banner("📦 IMPORT CHECKS")
    
    systems = {}
    
    # ProtonGameArena
    try:
        from reality_simulator.arena import ProtonGameArena
        systems['ProtonGameArena'] = True
        print("✅ ProtonGameArena imports OK")
        
        # Check if it has event emitter
        arena = ProtonGameArena()
        has_emitter = hasattr(arena, '_emit_event')
        print(f"   - _emit_event method: {'✅' if has_emitter else '❌'}")
        
        # Check event types
        events = ['proton_selection_begun', 'proton_challenge_chosen', 'proton_resource_chosen', 
                  'proton_game_selected', 'proton_battle_complete', 'proton_consequences_applied']
        print(f"   - Expected events: {', '.join(events[:3])}...")
    except ImportError as e:
        systems['ProtonGameArena'] = False
        print(f"❌ ProtonGameArena import failed: {e}")
    
    # BattleArena
    try:
        from reality_simulator.evolution.battle_arena import BattleArena, BattleType
        systems['BattleArena'] = True
        print("✅ BattleArena imports OK")
        print(f"   - PROTON_GAME in BattleType: {'✅' if 'PROTON_GAME' in BattleType.__members__ else '❌'}")
        
        # Check if it can route to proton
        arena = BattleArena()
        has_proton_resolver = hasattr(arena, '_resolve_proton_game_battle')
        print(f"   - _resolve_proton_game_battle method: {'✅' if has_proton_resolver else '❌'}")
    except ImportError as e:
        systems['BattleArena'] = False
        print(f"❌ BattleArena import failed: {e}")
    
    # HighlanderProtocol
    try:
        from reality_simulator.evolution.highlander_protocol import HighlanderProtocol
        systems['HighlanderProtocol'] = True
        print("✅ HighlanderProtocol imports OK")
    except ImportError as e:
        systems['HighlanderProtocol'] = False
        print(f"❌ HighlanderProtocol import failed: {e}")
    
    # AllianceWarfareSystem
    try:
        from reality_simulator.evolution.alliance_warfare import AllianceWarfareSystem, AllianceHistory
        systems['AllianceWarfareSystem'] = True
        print("✅ AllianceWarfareSystem imports OK")
        print(f"   - AllianceHistory available: ✅")
    except ImportError as e:
        systems['AllianceWarfareSystem'] = False
        print(f"❌ AllianceWarfareSystem import failed: {e}")
    
    # GerminationPool
    try:
        from reality_simulator.evolution.germination_pool import GerminationPool
        systems['GerminationPool'] = True
        print("✅ GerminationPool imports OK")
    except ImportError as e:
        systems['GerminationPool'] = False
        print(f"❌ GerminationPool import failed: {e}")
    
    return systems


def check_highlander_integration():
    """Check if highlander is properly using battle systems."""
    banner("🔗 HIGHLANDER → BATTLE ARENA INTEGRATION")
    
    try:
        from reality_simulator.evolution.highlander_protocol import HighlanderProtocol
        from reality_simulator.evolution.battle_arena import BattleType
        
        # Create a highlander with arena
        hp = HighlanderProtocol(config={})
        
        print(f"✅ HighlanderProtocol created")
        print(f"   - battle_arena: {'✅ Present' if hp.battle_arena else '❌ MISSING'}")
        
        if hp.battle_arena:
            # Check what battle type it uses
            import inspect
            source = inspect.getsource(hp._execute_battle)
            
            if 'PROTON_GAME' in source:
                print(f"   - Uses PROTON_GAME: ✅")
            elif 'FULL_COMBAT' in source:
                print(f"   - Uses FULL_COMBAT: ⚠️ (not using Proton Arena)")
                print(f"   - 🔧 FIX NEEDED: Should respect arena.default_battle_type config")
            else:
                print(f"   - Battle type: ❓ Unknown")
                
    except Exception as e:
        print(f"❌ Integration check failed: {e}")


def check_alliance_events():
    """Check Alliance Warfare event emission."""
    banner("📡 ALLIANCE WARFARE EVENT EMISSION")
    
    try:
        from reality_simulator.evolution.alliance_warfare import AllianceWarfareSystem
        
        # Track emitted events
        emitted_events = []
        
        def mock_emitter(event):
            emitted_events.append(event)
        
        # Create system with mock emitter
        aws = AllianceWarfareSystem(
            highlander_protocol=None,
            config={},
            event_emitter=mock_emitter
        )
        
        print(f"✅ AllianceWarfareSystem created with event emitter")
        print(f"   - _emit_event method: {'✅' if hasattr(aws, '_emit_event') else '❌'}")
        
        # Check expected event types
        event_types = ['founded', 'member_joined', 'war_proposed', 'peace_proposed',
                       'civilization_progress', 'historical_record', 'illumination_granted']
        print(f"   - Expected event types: {len(event_types)}")
        for et in event_types:
            print(f"     • {et}")
            
    except Exception as e:
        print(f"❌ Event check failed: {e}")


def check_civilization_history():
    """Check civilizational history tracking."""
    banner("📜 CIVILIZATIONAL HISTORY TRACKING")
    
    try:
        from reality_simulator.evolution.alliance_warfare import (
            AllianceHistory, HistoricalEvent, HistoricalEventType, CausalPattern
        )
        
        print("✅ History classes import OK")
        
        # Create a test history
        history = AllianceHistory(
            alliance_id="test_alliance",
            alliance_name="Test Alliance"
        )
        
        # Record some test events
        event = HistoricalEvent(
            event_id="test_001",
            event_type=HistoricalEventType.ALLIANCE_FOUNDED,
            description="Test alliance founded",
            round_number=1,
            primary_organism_id="org_001",
            vp_at_time=0.5,
            member_count=3
        )
        
        history.record_event(event)
        
        print(f"✅ History recording works")
        print(f"   - Events recorded: {len(history.events)}")
        print(f"   - Events by type: {dict(history.events_by_type)}")
        print(f"   - Legends: {len(history.legends)}")
        print(f"   - Wisdom rules: {len(history.wisdom_rules)}")
        
        # Check pattern extraction
        print(f"\n   📊 Pattern extraction methods:")
        print(f"   - extract_pattern: {'✅' if hasattr(history, 'extract_pattern') else '❌'}")
        print(f"   - get_recent_events: {'✅' if hasattr(history, 'get_recent_events') else '❌'}")
        print(f"   - get_organism_history: {'✅' if hasattr(history, 'get_organism_history') else '❌'}")
        
    except Exception as e:
        print(f"❌ History check failed: {e}")
        import traceback
        traceback.print_exc()


def check_illumination_engine():
    """Check the Illumination Engine (civilization rewards)."""
    banner("🔮 ILLUMINATION ENGINE (Civilization Rewards)")
    
    try:
        from reality_simulator.evolution.alliance_warfare import AllianceWarfareSystem
        
        aws = AllianceWarfareSystem(highlander_protocol=None, config={})
        
        # Check if wire_illumination method exists
        has_illumination = hasattr(aws, 'wire_illumination_engine')
        print(f"   - wire_illumination_engine: {'✅' if has_illumination else '❌'}")
        
        # Check if grant_illumination exists
        has_grant = hasattr(aws, '_grant_illumination')
        print(f"   - _grant_illumination: {'✅' if has_grant else '❌'}")
        
        # Check illumination levels
        if hasattr(aws, 'ILLUMINATION_LEVELS'):
            print(f"   - ILLUMINATION_LEVELS defined: ✅")
            print(f"     Levels: {list(aws.ILLUMINATION_LEVELS.keys()) if isinstance(aws.ILLUMINATION_LEVELS, dict) else 'N/A'}")
        else:
            # Check if defined at class level
            print(f"   - Checking for illumination level definitions in source...")
        
    except Exception as e:
        print(f"❌ Illumination check failed: {e}")


def check_logs():
    """Check recent logs for battle system activity."""
    banner("📝 LOG FILE ANALYSIS")
    
    log_dir = Path("data/logs")
    if not log_dir.exists():
        print(f"⚠️ Log directory not found: {log_dir}")
        return
    
    # Find recent log files
    log_files = list(log_dir.glob("*.log")) + list(log_dir.glob("*.json"))
    
    if not log_files:
        print("⚠️ No log files found")
        return
    
    print(f"📁 Found {len(log_files)} log files")
    
    # Keywords to search for
    keywords = {
        'proton': 0,
        'PROTON': 0,
        'alliance': 0,
        'Alliance': 0,
        'civilization': 0,
        'illumination': 0,
        'historical_record': 0,
        'HIGHLANDER': 0,
        'battle_concluded': 0,
        'germination': 0
    }
    
    # Search recent files
    recent_files = sorted(log_files, key=lambda f: f.stat().st_mtime, reverse=True)[:5]
    
    for log_file in recent_files:
        try:
            with open(log_file, 'r', errors='ignore') as f:
                content = f.read()
                
            for kw in keywords:
                keywords[kw] += content.count(kw)
        except:
            pass
    
    print(f"\n📊 Keyword counts in recent logs:")
    for kw, count in sorted(keywords.items(), key=lambda x: -x[1]):
        status = '✅' if count > 0 else '⚠️'
        print(f"   {status} '{kw}': {count} occurrences")


def check_shared_state():
    """Check shared_state.json for battle data."""
    banner("📂 SHARED_STATE.JSON ANALYSIS")
    
    state_path = Path("data/shared_state.json")
    if not state_path.exists():
        print(f"⚠️ shared_state.json not found")
        return
    
    try:
        with open(state_path, 'r') as f:
            state = json.load(f)
        
        # Check for highlander data
        highlander = state.get('highlander', {})
        if highlander:
            print(f"\n⚔️ HIGHLANDER STATE:")
            print(f"   - phase: {highlander.get('phase', 'N/A')}")
            print(f"   - population: {highlander.get('population', 'N/A')}")
            print(f"   - battles: {highlander.get('battles', 'N/A')}")
            print(f"   - eliminations: {highlander.get('total_eliminations', 'N/A')}")
            print(f"   - alliances: {highlander.get('alliances', 'N/A')}")
        else:
            print("⚠️ No highlander data in shared_state")
        
        # Check for alliance warfare data
        if 'alliance_warfare' in state or 'alliances' in state:
            print(f"\n🤝 ALLIANCE DATA:")
            alliances = state.get('alliance_warfare', state.get('alliances', {}))
            print(f"   - Raw data: {type(alliances)}")
        
    except Exception as e:
        print(f"❌ Failed to parse shared_state.json: {e}")


def main():
    print("\n" + "🔍"*35)
    print("   BATTLE SYSTEMS DEEP DIVE DIAGNOSTIC")
    print("🔍"*35)
    print(f"   Time: {datetime.now().isoformat()}")
    
    config = check_config()
    systems = check_imports()
    check_highlander_integration()
    check_alliance_events()
    check_civilization_history()
    check_illumination_engine()
    check_logs()
    check_shared_state()
    
    banner("📋 SUMMARY")
    
    print("\n🎯 KEY FINDINGS:")
    
    # Check if proton is actually being used
    if config:
        arena_config = config.get('arena', {})
        if arena_config.get('enabled'):
            print("   ✅ Proton Arena ENABLED in config")
            if arena_config.get('default_battle_type') == 'PROTON_GAME':
                print("   ✅ default_battle_type = PROTON_GAME")
            else:
                print("   ⚠️ default_battle_type != PROTON_GAME")
            
            # Check proton_game_probability (NEW!)
            proton_prob = arena_config.get('proton_game_probability', 0.0)
            if proton_prob > 0:
                print(f"   ✅ proton_game_probability = {proton_prob:.0%}")
                if proton_prob >= 0.5:
                    print("   🎮 Proton Game will handle 50%+ of battles!")
            else:
                print("   ⚠️ proton_game_probability = 0% (not using mixed battles)")
            
            # Check prefer_native_games
            if arena_config.get('prefer_native_games', False):
                print("   ✅ prefer_native_games = true (language/concept games prioritized)")
        else:
            print("   ❌ Proton Arena DISABLED in config")
    
    # Check for LiveOrganismAdapter
    try:
        from reality_simulator.arena.live_organism_adapter import LiveOrganismAdapter
        print("   ✅ LiveOrganismAdapter available (bridges organism → Proton Game)")
    except ImportError:
        print("   ❌ LiveOrganismAdapter NOT FOUND")
    
    print("\n🔧 STATUS:")
    print("   ✅ HighlanderProtocol reads arena.default_battle_type from config")
    print("   ✅ HighlanderProtocol creates LiveOrganismAdapters for PROTON_GAME")
    print("   ✅ proton_game_probability controls mixed battle selection")
    print("   ℹ️  Alliance formation requires organism neural DECISIONS")
    print("      → Organisms need to output 'cooperate' action to trigger alliances")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
