#!/usr/bin/env python3
"""
Simple test runner for thumbnail function tests
"""
import subprocess
import sys
import os

def run_test(test_name, test_file):
    """Run a specific test file"""
    print(f"\n🚀 Running {test_name}...")
    print("=" * 60)
    
    # Set PYTHONPATH to include the project root
    env = os.environ.copy()
    env['PYTHONPATH'] = '/Users/akshdeepsingh/PythonDev/Kliper_AI/Functions'
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            cwd='/Users/akshdeepsingh/PythonDev/Kliper_AI/Functions',
            env=env,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ {test_name} completed successfully")
        else:
            print(f"❌ {test_name} failed with exit code {result.returncode}")
            
    except Exception as e:
        print(f"❌ Error running {test_name}: {e}")


if __name__ == "__main__":
    print("🧪 Thumbnail Function Test Suite")
    print("=" * 60)
    
    # Test 1: Video thumbnail processing
    run_test("Video Thumbnail Test", "test/test_thumbnail_function.py")
    
    print("\n" + "=" * 60)
    print("🏁 Test suite completed!")
    print("\n📝 Note: Make sure your Azure Function is running and")
    print("   your .env file contains the correct database and storage credentials.")
