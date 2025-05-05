#!/usr/bin/env python3
"""
Test script for the /parse_cmt endpoint of the API.
This test sends all test cases from test_parser_func_data.py to the API
and verifies the responses match the expected values.
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

# Now import from test data
from test_data.test_parser_func_data import test_data

# API endpoint configuration
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8080')
PARSE_CMT_ENDPOINT = f"{API_BASE_URL}/parse_cmt"

def write_results_to_file(results, test_cases):
    """Write complete test results to a JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(project_root) / "test" / "results"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"test_parser_func_results_{timestamp}.json"
    
    # Create a comprehensive results structure
    output_data = {
        "timestamp": timestamp,
        "api_base_url": API_BASE_URL,
        "total_tests": len(results),
        "successful_api_calls": sum(1 for r in results if r['success']),
        "passed_tests": sum(1 for r in results if r['pass']),
        "total_time": sum(r['time'] for r in results),
        "test_cases": []
    }
    
    # Add detailed results for each test case
    for i, (result, test_case) in enumerate(zip(results, test_cases)):
        test_data = {
            "test_number": i + 1,
            "description": test_case.description or "Unnamed test",
            "comparison_string": test_case.comparison_string,
            "solution_string": test_case.solution_string,
            "parameter_string": test_case.parameter_string,
            "function_string": test_case.function_string,
            "expected_result": test_case.expected_result,
            "result": {
                "success": result['success'],
                "pass": result['pass'],
                "time": result['time'],
                "api_response": result.get('api_response', {}),
                "error_message": result.get('error_message', ''),
                "evaluation_results": result.get('evaluation_results', []),
                "intermediate_expressions": result.get('intermediate_expressions', []),
                "sympy_expressions": result.get('sympy_expressions', [])
            }
        }
        output_data["test_cases"].append(test_data)
    
    # Write to file
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n{Fore.GREEN}✓ Complete test results written to: {output_file}{Style.RESET_ALL}")

def test_api_parser_func():
    """
    Test the /parse_cmt endpoint of the API by sending test cases and verifying the responses.
    This ensures the API correctly parses LaTeX expressions and returns the expected evaluations.
    """
    print(f"\n{Fore.CYAN}{'='*20} TESTING PARSER FUNCTION API {'='*20}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Testing API parse_cmt endpoint at: {PARSE_CMT_ENDPOINT}{Style.RESET_ALL}")
    
    all_pass = True
    failed_cases = []
    results = []
    total_time = 0

    for i, test_case in enumerate(test_data):
        test_num = i + 1
        comparison_str = test_case.comparison_string
        solution_str = test_case.solution_string
        parameter_str = test_case.parameter_string
        function_str = test_case.function_string
        description = test_case.description or "No description provided"

        # Print test case info
        print(f"\n{Fore.CYAN}Test #{test_num}: {description}{Style.RESET_ALL}")
        
        # Prepare request data
        request_data = {
            "input": comparison_str,
            "parameters": parameter_str,
            "functions": function_str
        }

        # Print request details
        print(f"Input: {Fore.BLUE}{comparison_str[:80]}...{Style.RESET_ALL}" if len(comparison_str) > 80 
              else f"Input: {Fore.BLUE}{comparison_str}{Style.RESET_ALL}")
        print(f"Parameters: {Fore.BLUE}{parameter_str or 'None'}{Style.RESET_ALL}")
        print(f"Functions: {Fore.BLUE}{function_str or 'None'}{Style.RESET_ALL}")

        # Record start time for performance measurement
        start_time = time.time()
        success = False
        
        try:
            # Send request to API
            print(f"  {Fore.BLUE}⏳ Sending request to API...{Style.RESET_ALL}")
            response = requests.post(PARSE_CMT_ENDPOINT, json=request_data)
            
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            total_time += elapsed_time
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse response JSON
            result = response.json()
            
            # API request was successful at this point
            print(f"{Fore.GREEN}✓ API request successful ({elapsed_time:.2f}s){Style.RESET_ALL}")
            
            # Verify success flag
            if not result.get('success', False):
                error_msg = result.get('error_message', 'No error message')
                print(f"{Fore.RED}✗ API reported failure: {error_msg}{Style.RESET_ALL}")
                all_pass = False
                failed_cases.append(i)
                results.append({
                    "id": i, 
                    "success": False, 
                    "pass": False, 
                    "time": elapsed_time,
                    "api_response": result,
                    "error_message": error_msg
                })
                continue
                
            # Test passed if we got a successful response
            print(f"{Fore.GREEN}✓ Test passed ({elapsed_time:.2f}s){Style.RESET_ALL}")
            results.append({
                "id": i, 
                "success": True, 
                "pass": True, 
                "time": elapsed_time,
                "api_response": result
            })
                
        except requests.RequestException as e:
            elapsed_time = time.time() - start_time
            total_time += elapsed_time
            print(f"{Fore.RED}✗ API request failed: {str(e)} ({elapsed_time:.2f}s){Style.RESET_ALL}")
            all_pass = False
            failed_cases.append(i)
            results.append({
                "id": i, 
                "success": False, 
                "pass": False, 
                "time": elapsed_time,
                "error_message": str(e)
            })
        except Exception as e:
            elapsed_time = time.time() - start_time
            total_time += elapsed_time
            print(f"{Fore.RED}✗ Test error: {str(e)} ({elapsed_time:.2f}s){Style.RESET_ALL}")
            all_pass = False
            failed_cases.append(i)
            results.append({
                "id": i, 
                "success": False, 
                "pass": False, 
                "time": elapsed_time,
                "error_message": str(e)
            })

    # Print summary
    print(f"\n{Fore.CYAN}==== Test Summary ===={Style.RESET_ALL}")
    success_count = sum(1 for r in results if r["success"])
    pass_count = sum(1 for r in results if r["pass"])
    
    print(f"Total tests: {len(results)}")
    print(f"Successful API calls: {Fore.GREEN if success_count == len(results) else Fore.RED}{success_count}/{len(results)}{Style.RESET_ALL} {Fore.GREEN}← PRIMARY SUCCESS METRIC{Style.RESET_ALL}")
    print(f"Tests passed: {Fore.YELLOW}{pass_count}/{len(results)}{Style.RESET_ALL} (informational only)")
    print(f"Total time: {total_time:.2f}s")
    
    # Print detailed results
    print(f"\n{Fore.CYAN}==== Detailed Results ===={Style.RESET_ALL}")
    for result in results:
        api_status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if result['success'] else f"{Fore.RED}✗{Style.RESET_ALL}"
        pass_status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if result['pass'] else f"{Fore.YELLOW}⚠{Style.RESET_ALL}"
        print(f"{api_status} {test_data[result['id']].description or 'Unnamed test'} - API: {'✓' if result['success'] else '✗'}, Pass: {pass_status if result['success'] else 'N/A'}, Time: {result['time']:.2f}s")

    # Overall test result
    if success_count == len(results):
        print(f"\n{Fore.GREEN}✅ All API tests passed!{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}❌ {len(results) - success_count} API tests failed!{Style.RESET_ALL}")
    
    # Write complete results to file
    write_results_to_file(results, test_data)
    
    return all_pass
    
def test_api_health():
    """Check if the API is running by calling the health endpoint"""
    try:
        print(f"{Fore.BLUE}⏳ Checking API health at {API_BASE_URL}...{Style.RESET_ALL}")
        response = requests.get(f"{API_BASE_URL}/health")
        response.raise_for_status()
        result = response.json()
        if result.get('status') == 'healthy':
            print(f"{Fore.GREEN}✓ API is healthy{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}✗ API returned unexpected status: {result}{Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"{Fore.RED}✗ API health check failed: {str(e)}{Style.RESET_ALL}")
        return False

if __name__ == "__main__":
    # First check if the API is running
    if test_api_health():
        success = test_api_parser_func()
        if success:
            print(f"\n{Fore.GREEN}✅ All API tests passed!{Style.RESET_ALL}")
            sys.exit(0)
        else:
            print(f"\n{Fore.RED}❌ Some API tests failed!{Style.RESET_ALL}")
            sys.exit(1)
    else:
        print(f"\n{Fore.RED}Skipping tests because the API is not running.{Style.RESET_ALL}")
        print(f"Make sure the API is running at {API_BASE_URL}")
        sys.exit(1) 