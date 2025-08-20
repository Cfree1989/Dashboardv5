#!/usr/bin/env python3
import subprocess
import sys

def run_single_test(test_path):
    """Run a single pytest test in isolation with detailed output"""
    cmd = ["pytest", test_path, "-v", "-s", "--tb=long"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: debug_single_test.py <test_path>")
        sys.exit(1)
    test_path = sys.argv[1]
    res = run_single_test(test_path)
    print(f"Exit code: {res.returncode}")
    print("STDOUT:")
    print(res.stdout)
    print("STDERR:")
    print(res.stderr)
