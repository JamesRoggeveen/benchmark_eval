#!/usr/bin/env python3
"""
Script to run test_eval_*.json files through the /eval endpoint of the API.
"""

import os
import sys
import json
import glob
import requests
import time
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# API endpoint configuration
# API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8080')
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:5000')
EVAL_ENDPOINT = f"{API_BASE_URL}/eval_cmt_numerics"

def check_api_health():
    """Check if the API is running by calling the health endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        response.raise_for_status()
        result = response.json()
        if result.get('status') == 'healthy':
            print(f"{Fore.GREEN}✓ API is healthy at {API_BASE_URL}{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}✗ API returned unexpected status: {result}{Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"{Fore.RED}✗ API health check failed: {str(e)}{Style.RESET_ALL}")
        return False

def find_test_files():
    """Find all test_eval_*.json files in the test_data directory"""
    test_dir = Path(project_root) / "test" / "test_data"
    test_files = list(test_dir.glob("test_eval*cmt*.json"))
    
    if not test_files:
        print(f"{Fore.YELLOW}No test_eval*cmt*.json files found in {test_dir}{Style.RESET_ALL}")
        # Also look for any JSON files as a fallback
        test_files = list(test_dir.glob("*cmt*.json"))
        if test_files:
            print(f"{Fore.YELLOW}Found {len(test_files)} other JSON files that might be suitable for testing{Style.RESET_ALL}")
    
    return sorted(test_files)

def run_test(test_file):
    """Run a single test file through the /eval endpoint"""
    print(f"\n{Fore.CYAN}Running test: {test_file.name}{Style.RESET_ALL}")
    
    try:
        # Load test data from JSON file
        with open(test_file, 'r') as f:
            test_data = json.load(f)
        
        # Print request details
        print(f"Model: {Fore.BLUE}{test_data.get('model', 'Not specified')}{Style.RESET_ALL}")
        print(f"Parameters: {Fore.BLUE}{test_data.get('parameters', 'None')}{Style.RESET_ALL}")
        print(f"Input prompt: {Fore.BLUE}{test_data['input'][:80]}...{Style.RESET_ALL}" if len(test_data['input']) > 80 
              else f"Input prompt: {Fore.BLUE}{test_data['input']}{Style.RESET_ALL}")
        
        # Record start time for performance measurement
        start_time = time.time()
        
        # Send request to API
        response = requests.post(EVAL_ENDPOINT, json=test_data)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse response JSON
        result = response.json()
        
        # API request was successful at this point, regardless of evaluation result
        print(f"{Fore.GREEN}✓ API request successful ({elapsed_time:.2f}s){Style.RESET_ALL}")
        
        # Get equivalence result (optional information)
        is_equivalent = result.get('is_equivalent', False)
        if is_equivalent:
            print(f"{Fore.GREEN}✓ Solutions are equivalent{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠ Solutions are NOT equivalent (but API worked successfully){Style.RESET_ALL}")
        
        # Print model response snippet
        model_response = result.get('model_response', '')
        if model_response:
            print(f"\nModel response snippet:\n{Fore.YELLOW}{model_response[:200]}...{Style.RESET_ALL}" 
                  if len(model_response) > 200 else f"\nModel response:\n{Fore.YELLOW}{model_response}{Style.RESET_ALL}")
        
        # Print evaluation results
        solution_results = result.get('solution', {}).get('evaluation_results', [])
        model_results = result.get('model', {}).get('evaluation_results', [])
        
        if solution_results and model_results:
            print("\nEvaluation results:")
            print(f"  Solution: {Fore.CYAN}{solution_results}{Style.RESET_ALL}")
            print(f"  Model:    {Fore.CYAN}{model_results}{Style.RESET_ALL}")
        
        # Always return API success as the primary result
        return True, is_equivalent, elapsed_time
            
    except requests.RequestException as e:
        print(f"{Fore.RED}✗ API request error: {str(e)}{Style.RESET_ALL}")
        return False, False, 0
    except Exception as e:
        print(f"{Fore.RED}✗ Test error: {str(e)}{Style.RESET_ALL}")
        return False, False, 0

def run_all_tests():
    """Find and run all test files through the API"""
    # Check if API is running
    if not check_api_health():
        print(f"{Fore.RED}Skipping tests because the API is not running.{Style.RESET_ALL}")
        print(f"Make sure the API is running at {API_BASE_URL}")
        return
    
    # Find test files
    test_files = find_test_files()
    if not test_files:
        print(f"{Fore.RED}No test files found. Exiting.{Style.RESET_ALL}")
        return
    
    print(f"{Fore.GREEN}Found {len(test_files)} test files{Style.RESET_ALL}")
    
    # Run each test file
    results = []
    for test_file in test_files:
        success, is_equivalent, elapsed_time = run_test(test_file)
        results.append({
            'file': test_file.name,
            'success': success,
            'equivalent': is_equivalent,
            'elapsed_time': elapsed_time
        })
    
    # Print summary
    print(f"\n{Fore.CYAN}==== Test Summary ===={Style.RESET_ALL}")
    successful_api_calls = sum(1 for r in results if r['success'])
    equivalent_solutions = sum(1 for r in results if r['equivalent'])
    total_time = sum(r['elapsed_time'] for r in results)
    
    print(f"Total tests: {len(results)}")
    print(f"Successful API calls: {Fore.GREEN if successful_api_calls == len(results) else Fore.RED}{successful_api_calls}/{len(results)}{Style.RESET_ALL} {Fore.GREEN}← PRIMARY SUCCESS METRIC{Style.RESET_ALL}")
    print(f"Equivalent solutions: {Fore.YELLOW}{equivalent_solutions}/{len(results)}{Style.RESET_ALL} (informational only)")
    print(f"Total time: {total_time:.2f}s")
    
    # Print detailed results
    print(f"\n{Fore.CYAN}==== Detailed Results ===={Style.RESET_ALL}")
    for result in results:
        api_status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if result['success'] else f"{Fore.RED}✗{Style.RESET_ALL}"
        equiv_status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if result['equivalent'] else f"{Fore.YELLOW}⚠{Style.RESET_ALL}"
        print(f"{api_status} {result['file']} - API: {'✓' if result['success'] else '✗'}, Equivalent: {equiv_status if result['success'] else 'N/A'}, Time: {result['elapsed_time']:.2f}s")

    # Overall test result
    if successful_api_calls == len(results):
        print(f"\n{Fore.GREEN}✅ All API tests passed!{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}❌ {len(results) - successful_api_calls} API tests failed!{Style.RESET_ALL}")

if __name__ == "__main__":
    run_all_tests() 