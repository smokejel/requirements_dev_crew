#!/usr/bin/env python3
"""
Test runner for CrewAI Requirements Decomposer API tests.

This script provides convenient test execution with different configurations.
"""

import os
import sys
import subprocess
import argparse
import time
import requests
from pathlib import Path

def check_server_health(base_url="http://localhost:8000", timeout=30):
    """Check if the API server is running and healthy."""
    print(f"Checking server health at {base_url}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    print("✅ Server is healthy and ready for testing")
                    return True
            print(f"❌ Server responded but not healthy: {response.status_code}")
        except requests.exceptions.RequestException:
            print("⏳ Server not ready, waiting...")
            time.sleep(2)
    
    print(f"❌ Server not available after {timeout} seconds")
    return False

def run_tests(test_args):
    """Run pytest with the given arguments."""
    cmd = ["pytest"] + test_args
    
    print(f"Running: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Run CrewAI Requirements Decomposer API tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                     # Run all tests
  python run_tests.py --fast              # Run only fast tests
  python run_tests.py --basic             # Run only basic API tests
  python run_tests.py --websocket         # Run only WebSocket tests
  python run_tests.py --integration       # Run only integration tests
  python run_tests.py --with-api-keys     # Run tests requiring real API keys
  python run_tests.py --coverage          # Run with coverage report
  python run_tests.py --verbose           # Run with verbose output
  python run_tests.py --file test_api_basic.py  # Run specific test file
        """
    )
    
    # Test selection options
    parser.add_argument("--fast", action="store_true", 
                       help="Run only fast tests (exclude slow tests)")
    parser.add_argument("--basic", action="store_true", 
                       help="Run only basic API tests")
    parser.add_argument("--files", action="store_true", 
                       help="Run only file operation tests")
    parser.add_argument("--crew", action="store_true", 
                       help="Run only crew execution tests")
    parser.add_argument("--websocket", action="store_true", 
                       help="Run only WebSocket tests")
    parser.add_argument("--integration", action="store_true", 
                       help="Run only integration tests")
    parser.add_argument("--with-api-keys", action="store_true", 
                       help="Run tests requiring real API keys")
    parser.add_argument("--file", type=str, 
                       help="Run specific test file")
    
    # Output options
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output")
    parser.add_argument("--coverage", action="store_true", 
                       help="Run with coverage report")
    parser.add_argument("--quiet", "-q", action="store_true", 
                       help="Minimal output")
    
    # Advanced options
    parser.add_argument("--no-server-check", action="store_true", 
                       help="Skip server health check")
    parser.add_argument("--base-url", default="http://localhost:8000", 
                       help="Base URL for API server")
    parser.add_argument("--timeout", type=int, default=30, 
                       help="Server health check timeout")
    
    args = parser.parse_args()
    
    # Check server health unless disabled
    if not args.no_server_check:
        if not check_server_health(args.base_url, args.timeout):
            print("\n❌ Server is not running or not healthy.")
            print("Please start the server first:")
            print("  cd src")
            print("  uv run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload")
            print("\nIf you haven't installed test dependencies yet:")
            print("  uv pip install -e \".[test]\"")
            sys.exit(1)
    
    # Build pytest arguments
    pytest_args = ["tests/"]
    
    # Test selection
    if args.fast:
        pytest_args.extend(["-m", "not slow"])
    elif args.basic:
        pytest_args = ["tests/test_api_basic.py"]
    elif args.files:
        pytest_args = ["tests/test_file_operations.py"]
    elif args.crew:
        pytest_args = ["tests/test_crew_execution.py"]
    elif args.websocket:
        pytest_args.extend(["-m", "websocket"])
    elif args.integration:
        pytest_args.extend(["-m", "integration"])
    elif args.file:
        pytest_args = [f"tests/{args.file}"]
    
    # API key tests
    if args.with_api_keys:
        os.environ["ENABLE_API_KEY_TESTS"] = "1"
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  OPENAI_API_KEY not set. Real API key tests may fail.")
    
    # Output options
    if args.verbose:
        pytest_args.append("-v")
    if args.quiet:
        pytest_args.append("-q")
    if args.coverage:
        pytest_args.extend(["--cov=src/api", "--cov-report=html", "--cov-report=term"])
    
    # Run tests
    success = run_tests(pytest_args)
    
    if success:
        print("\n✅ All tests passed!")
        if args.coverage:
            print("📊 Coverage report generated in htmlcov/")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()