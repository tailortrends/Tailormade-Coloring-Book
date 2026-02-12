#!/usr/bin/env python3
"""
Master Health Check Script

Runs all API verification scripts and provides a comprehensive system health report.

Usage:
    python tools/health_check.py
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


def run_verification_script(script_name, description):
    """Run a verification script and capture results."""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"{'=' * 60}")
    
    script_path = Path(__file__).parent / script_name
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,  # Show output in real-time
            text=True
        )
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run {script_name}: {e}")
        return False


def main():
    """Run all health checks."""
    print("=" * 80)
    print(" " * 20 + "🏥 TAILORMADE SYSTEM HEALTH CHECK")
    print("=" * 80)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print(f"Python: {sys.version.split()[0]}")
    
    # Define all verification scripts
    checks = [
        ("verify_firebase.py", "Firebase (Auth + Firestore)"),
        ("verify_r2.py", "Cloudflare R2 (Object Storage)"),
        ("verify_fal.py", "fal.ai (Image Generation)"),
        ("verify_anthropic.py", "Anthropic Claude (Content Safety)")
    ]
    
    results = {}
    
    # Run each verification script
    for script_name, description in checks:
        results[description] = run_verification_script(script_name, description)
    
    # Final summary
    print("\n" + "=" * 80)
    print(" " * 30 + "FINAL SUMMARY")
    print("=" * 80)
    
    for service, passed in results.items():
        status = "✅ HEALTHY" if passed else "❌ FAILED"
        print(f"{status:12} - {service}")
    
    all_passed = all(results.values())
    partial_pass = any(results.values()) and not all_passed
    
    print("\n" + "=" * 80)
    
    if all_passed:
        print("✅ ALL SYSTEMS OPERATIONAL")
        print("   TailorMade is ready for production use.")
        print("=" * 80)
        sys.exit(0)
    elif partial_pass:
        print("⚠️  PARTIAL SYSTEM HEALTH")
        print("   Some services are unavailable but system may still function.")
        print("   Review failed checks above for details.")
        print("=" * 80)
        sys.exit(1)
    else:
        print("❌ CRITICAL SYSTEM FAILURE")
        print("   Multiple services are unavailable.")
        print("   Please review errors and check configuration.")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
