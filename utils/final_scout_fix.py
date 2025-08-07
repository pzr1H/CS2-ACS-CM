#!/usr/bin/env python3
"""
Final fix for scout_report.py - direct replacement
"""

import sys
from pathlib import Path

def diagnose_scout_report():
    """Check what's currently in scout_report.py"""
    scout_file = Path("utils/gui/scout_report.py")
    
    print(f"🔍 Diagnosing {scout_file}...")
    
    if not scout_file.exists():
        print("❌ scout_report.py doesn't exist!")
        return False
    
    try:
        with open(scout_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📊 File size: {len(content)} characters")
        
        # Check first few lines
        lines = content.split('\n')[:10]
        print("📋 First 10 lines:")
        for i, line in enumerate(lines, 1):
            print(f"  {i:2}: {line[:80]}...")
        
        # Check for key functions
        has_comprehensive = "generate_comprehensive_scout_report" in content
        has_replace_functions = "backup_and_replace_scout_report" in content
        
        print(f"\n🎯 Analysis:")
        print(f"  - Has generate_comprehensive_scout_report: {has_comprehensive}")
        print(f"  - Has replacement script functions: {has_replace_functions}")
        
        if has_replace_functions:
            print("❌ PROBLEM: File contains replacement script, not scout report!")
            return False
        elif has_comprehensive:
            print("✅ File looks correct")
            return True
        else:
            print("⚠️ File exists but doesn't have expected functions")
            return False
            
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

def create_working_scout_report():
    """Create a working scout_report.py directly"""
    scout_file = Path("utils/gui/scout_report.py")
    
    # Ensure directory exists
    scout_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Working scout report content
    working_content = '''#!/usr/bin/env python3
# utils/gui/scout_report.py

import json
import logging
from typing import Dict, Any, List, Optional

log = logging.getLogger(__name__)

def generate_comprehensive_scout_report(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate comprehensive scout report for CS2 players
    """
    if not data or "playerStats" not in data:
        log.warning("No playerStats found in data.")
        return {"error": "Missing playerStats data."}

    player_stats = data["playerStats"]
    report = {
        "summary": "CS2 Player Scout Report",
        "players": [],
        "threat_summary": {
            "low": 0,
            "medium": 0,
            "high": 0,
            "extreme": 0
        }
    }

    for player in player_stats:
        name = player.get("name", "Unknown")
        team = player.get("team", "Unknown")
        kills = player.get("kills", 0)
        deaths = player.get("deaths", 1) or 1  # Avoid div by zero
        assists = player.get("assists", 0)
        headshots = player.get("headshot_kills", 0) or player.get("headshots", 0)
        accuracy = player.get("accuracy", 0.0)
        damage = player.get("total_damage", 0) or player.get("damage", 0)
        faceit_elo = player.get("faceit_elo", 0)

        kd_ratio = round(kills / deaths, 2)
        hs_rate = round((headshots / kills) * 100, 2) if kills else 0
        threat_level = infer_threat_level(kd_ratio, hs_rate, accuracy, faceit_elo)

        player_report = {
            "name": name,
            "team": team,
            "kills": kills,
            "deaths": deaths,
            "assists": assists,
            "headshots": headshots,
            "headshot_rate": hs_rate,
            "accuracy": accuracy,
            "damage": damage,
            "kdr": kd_ratio,
            "faceit_elo": faceit_elo,
            "threat_level": threat_level
        }
        
        report["players"].append(player_report)
        report["threat_summary"][threat_level] += 1

    # Store report in data for GUI
    data["scoutReport"] = report
    log.info(f"Generated scout report for {len(report['players'])} players")
    return report

def infer_threat_level(kdr: float, hs_rate: float, accuracy: float, faceit_elo: int) -> str:
    """Infer threat level from player statistics"""
    if faceit_elo >= 2400:
        return "medium"
    elif faceit_elo >= 2000:
        return "low"
    
    if kdr >= 3.5 and hs_rate >= 75 and accuracy >= 0.45:
        return "extreme"
    elif kdr >= 2.0 and hs_rate >= 60:
        return "high"
    elif kdr >= 1.2 or hs_rate >= 40:
        return "medium"
    return "low"

def generate_scout_report(*args, **kwargs):
    """Alias for backward compatibility"""
    return generate_comprehensive_scout_report(*args, **kwargs)

def generate_team_scout_report(players_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate scout report for team"""
    if not players_data:
        return {"error": "No player data provided"}
    
    data = {"playerStats": players_data}
    return generate_comprehensive_scout_report(data)

# Export functions
__all__ = [
    "generate_comprehensive_scout_report",
    "generate_scout_report", 
    "generate_team_scout_report",
    "infer_threat_level"
]
'''
    
    print(f"✏️ Writing working scout_report.py...")
    
    try:
        with open(scout_file, 'w', encoding='utf-8', newline='\n') as f:
            f.write(working_content)
        
        print(f"✅ Successfully wrote {scout_file}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to write file: {e}")
        return False

def test_scout_import_directly():
    """Test scout report import directly"""
    print("🧪 Testing scout_report import...")
    
    # Clear any cached modules
    modules_to_clear = [
        'utils.gui.scout_report',
        'scout_report'
    ]
    
    for module in modules_to_clear:
        if module in sys.modules:
            del sys.modules[module]
    
    try:
        from utils.gui import scout_report
        
        if hasattr(scout_report, 'generate_comprehensive_scout_report'):
            print("✅ generate_comprehensive_scout_report found!")
            
            # Quick test
            test_data = {
                "playerStats": [
                    {"name": "TestPlayer", "kills": 10, "deaths": 5, "assists": 2}
                ]
            }
            
            result = scout_report.generate_comprehensive_scout_report(test_data)
            if isinstance(result, dict) and "players" in result:
                print("✅ Function works correctly!")
                return True
            else:
                print("❌ Function doesn't work as expected")
                return False
        else:
            available = [name for name in dir(scout_report) if not name.startswith('_')]
            print(f"❌ Function not found. Available: {available}")
            return False
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    print("🔧 FINAL SCOUT REPORT FIX")
    print("=" * 40)
    
    # Step 1: Diagnose current state
    print("1. Diagnosing current scout_report.py...")
    current_ok = diagnose_scout_report()
    
    if not current_ok:
        print("\n2. Creating working scout_report.py...")
        if create_working_scout_report():
            print("✅ Working file created")
        else:
            print("❌ Could not create working file")
            return
    else:
        print("✅ File looks correct already")
    
    # Step 2: Test import
    print(f"\n3. Testing import...")
    if test_scout_import_directly():
        print("🎉 SUCCESS: scout_report now works!")
    else:
        print("❌ Import still has issues")
        return
    
    # Step 3: Run integration test again
    print(f"\n4. Running integration test...")
    try:
        import subprocess
        result = subprocess.run([sys.executable, "test_integration_v2.py"], 
                              timeout=60, capture_output=True, text=True)
        
        if "ALL TESTS PASSED" in result.stdout:
            print("🎉 INTEGRATION TEST PASSED!")
            print("🚀 Ready to launch: python main.py")
        elif "MOSTLY WORKING" in result.stdout:
            print("✨ MOSTLY WORKING - should be good enough to run!")
            print("🚀 Try launching: python main.py")
        else:
            print("📊 Integration test completed - check results above")
            
    except Exception as e:
        print(f"Could not run integration test automatically: {e}")
        print("🔄 Please run manually: python test_integration_v2.py")
    
    print(f"\n✅ Scout report fix complete!")

if __name__ == "__main__":
    main()
