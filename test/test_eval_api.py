#!/usr/bin/env python3
"""
Script to run evaluation tests through the /eval endpoint of the API.
"""

import os
import sys
import json
import requests
import time
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Import test data
from test_data.test_eval_data import get_enabled_tests, to_json

# API endpoint configuration
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8080')
EVAL_ENDPOINT = f"{API_BASE_URL}/eval_cmt"

def write_results_to_file(results, test_cases):
    """Write complete test results to a JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(project_root) / "test" / "results"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"test_results_{timestamp}.json"
    
    # Create a comprehensive results structure
    output_data = {
        "timestamp": timestamp,
        "api_base_url": API_BASE_URL,
        "total_tests": len(results),
        "successful_api_calls": sum(1 for r in results if r['success']),
        "equivalent_solutions": sum(1 for r in results if r['equivalent']),
        "total_time": sum(r['elapsed_time'] for r in results),
        "test_cases": []
    }
    
    # Add detailed results for each test case
    for i, (result, test_case) in enumerate(zip(results, test_cases)):
        test_data = {
            "test_number": i + 1,
            "description": test_case.description or "Unnamed test",
            "input": test_case.input,
            "solution": test_case.solution,
            "parameters": test_case.parameters,
            "functions": test_case.functions,
            "model": test_case.model,
            "enabled": test_case.enabled,
            "result": {
                "success": result['success'],
                "equivalent": result['equivalent'],
                "elapsed_time": result['elapsed_time'],
                "api_response": result.get('api_response', {}),
                "model_response": result.get('model_response', ''),
                "error_message": result.get('error_message', ''),
                "evaluation_results": {
                    "solution": result.get('solution', {}).get('evaluation_results', []),
                    "model": result.get('model', {}).get('evaluation_results', [])
                },
                "intermediate_expressions": {
                    "solution": result.get('solution', {}).get('intermediate_expressions', []),
                    "model": result.get('model', {}).get('intermediate_expressions', [])
                },
                "sympy_expressions": {
                    "solution": result.get('solution', {}).get('sympy_expressions', []),
                    "model": result.get('model', {}).get('sympy_expressions', [])
                }
            }
        }
        output_data["test_cases"].append(test_data)
    
    # Write to file
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n{Fore.GREEN}✓ Complete test results written to: {output_file}{Style.RESET_ALL}")

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

def run_test(test_case):
    """Run a single test through the /eval endpoint"""
    print(f"\n{Fore.CYAN}Running test: {test_case.description or 'Unnamed test'}{Style.RESET_ALL}")
    
    try:
        # Convert test case to JSON format
        test_data = to_json(test_case)
        
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
        
        # Print success status and any error messages
        print(f"API Success: {Fore.GREEN if result.get('success') else Fore.RED}{result.get('success', False)}{Style.RESET_ALL}")
        if not result.get('success'):
            print(f"{Fore.RED}Error message: {result.get('error_message', 'No error message provided')}{Style.RESET_ALL}")
        
        # Get equivalence result (optional information)
        is_equivalent = result.get('is_equivalent', False)
        if is_equivalent:
            print(f"{Fore.GREEN}✓ Solutions are equivalent{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠ Solutions are NOT equivalent{Style.RESET_ALL}")
            # Print detailed information for non-equivalent cases
            print("\nDetailed comparison:")
            print(f"  Model success: {Fore.BLUE}{result.get('model', {}).get('success', False)}{Style.RESET_ALL}")
            if result.get('model', {}).get('error_message'):
                print(f"  Model error: {Fore.RED}{result['model']['error_message']}{Style.RESET_ALL}")
            
            print(f"  Solution success: {Fore.BLUE}{result.get('solution', {}).get('success', False)}{Style.RESET_ALL}")
            if result.get('solution', {}).get('error_message'):
                print(f"  Solution error: {Fore.RED}{result['solution']['error_message']}{Style.RESET_ALL}")
            
            # Print any top-level error message
            if result.get('error_message'):
                print(f"  Comparison error: {Fore.RED}{result['error_message']}{Style.RESET_ALL}")
        
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
            
            # Print intermediate expressions for debugging non-equivalent cases
            if not is_equivalent:
                print("\nIntermediate expressions:")
                print(f"  Solution: {Fore.CYAN}{result.get('solution', {}).get('intermediate_expressions', [])}{Style.RESET_ALL}")
                print(f"  Model:    {Fore.CYAN}{result.get('model', {}).get('intermediate_expressions', [])}{Style.RESET_ALL}")
                print("\nSymPy expressions:")
                print(f"  Solution: {Fore.CYAN}{result.get('solution', {}).get('sympy_expressions', [])}{Style.RESET_ALL}")
                print(f"  Model:    {Fore.CYAN}{result.get('model', {}).get('sympy_expressions', [])}{Style.RESET_ALL}")
        
        # Return complete result data for file output
        return True, is_equivalent, elapsed_time, result
            
    except requests.RequestException as e:
        print(f"{Fore.RED}✗ API request error: {str(e)}{Style.RESET_ALL}")
        return False, False, 0, {"error": str(e)}
    except Exception as e:
        print(f"{Fore.RED}✗ Test error: {str(e)}{Style.RESET_ALL}")
        return False, False, 0, {"error": str(e)}

def run_all_tests():
    """Run all enabled test cases through the API"""
    # Check if API is running
    if not check_api_health():
        print(f"{Fore.RED}Skipping tests because the API is not running.{Style.RESET_ALL}")
        print(f"Make sure the API is running at {API_BASE_URL}")
        return
    
    # Get enabled test cases
    test_cases = get_enabled_tests()
    if not test_cases:
        print(f"{Fore.RED}No enabled test cases found. Exiting.{Style.RESET_ALL}")
        return
    
    print(f"{Fore.GREEN}Found {len(test_cases)} enabled test cases{Style.RESET_ALL}")
    
    # Run each test case
    results = []
    for test_case in test_cases:
        success, is_equivalent, elapsed_time, api_response = run_test(test_case)
        results.append({
            'description': test_case.description or 'Unnamed test',
            'success': success,
            'equivalent': is_equivalent,
            'elapsed_time': elapsed_time,
            'api_response': api_response
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
        print(f"{api_status} {result['description']} - API: {'✓' if result['success'] else '✗'}, Equivalent: {equiv_status if result['success'] else 'N/A'}, Time: {result['elapsed_time']:.2f}s")

    # Overall test result
    if successful_api_calls == len(results):
        print(f"\n{Fore.GREEN}✅ All API tests passed!{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}❌ {len(results) - successful_api_calls} API tests failed!{Style.RESET_ALL}")
    
    # Write complete results to file
    write_results_to_file(results, test_cases)

if __name__ == "__main__":
    run_all_tests() 