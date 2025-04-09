#!/usr/bin/env python3
"""
Test script for the /parse endpoint of the API.
This test sends all test cases from test_parser_data.py to the API
and verifies the responses match the expected values.
"""

import os
import sys
import numpy as np
import requests
import json
import re
import time
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Now import from test data
from test_data.test_parser_data import test_data, TestParserData

# API endpoint configuration
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8080')
PARSE_ENDPOINT = f"{API_BASE_URL}/parse"

def is_complex_string(value):
    """Check if a string represents a complex number"""
    if not isinstance(value, str):
        return False
    # Match patterns like "(1+2j)" or "1+2j" or "(1-2j)" or "1-2j"
    return bool(re.search(r'.*[+-].*j.*', value))

def convert_to_complex(value):
    """Convert a value to complex if it's a string representation of a complex number"""
    if isinstance(value, str) and is_complex_string(value):
        # Replace parentheses if they exist
        cleaned = value.replace('(', '').replace(')', '')
        try:
            return complex(cleaned)
        except ValueError:
            print(f"{Fore.YELLOW}⚠ Warning: Failed to convert '{value}' to complex{Style.RESET_ALL}")
            return value
    return value

def compare_results(api_results, expected_results):
    """
    Compare API results with expected results, handling complex numbers.
    
    Returns:
        tuple: (is_equal, error_message)
    """
    if len(api_results) != len(expected_results):
        return False, f"Result length mismatch: got {len(api_results)}, expected {len(expected_results)}"
    
    # Convert all values to appropriate types
    converted_api = []
    converted_expected = []
    
    for i in range(len(api_results)):
        api_val = convert_to_complex(api_results[i])
        expected_val = expected_results[i]
        
        # Ensure expected value is also complex if needed
        if isinstance(api_val, complex) and not isinstance(expected_val, complex):
            try:
                expected_val = complex(expected_val)
            except (ValueError, TypeError):
                pass
                
        converted_api.append(api_val)
        converted_expected.append(expected_val)
    
    # Now compare the values
    try:
        if all(isinstance(val, complex) for val in converted_api + converted_expected):
            # For all complex values, use numpy allclose
            api_array = np.array(converted_api, dtype=complex)
            expected_array = np.array(converted_expected, dtype=complex)
            is_equal = np.allclose(api_array, expected_array)
        else:
            # Mixed types, compare individually
            is_equal = True
            for api_val, expected_val in zip(converted_api, converted_expected):
                if isinstance(api_val, complex) or isinstance(expected_val, complex):
                    # Convert both to complex for comparison
                    try:
                        api_complex = complex(api_val)
                        expected_complex = complex(expected_val)
                        val_equal = np.allclose(api_complex, expected_complex)
                    except (ValueError, TypeError):
                        val_equal = False
                else:
                    # Regular float comparison
                    val_equal = np.allclose(float(api_val), float(expected_val))
                
                if not val_equal:
                    is_equal = False
                    break
                    
        return is_equal, "" if is_equal else f"Values differ: {converted_api} vs {converted_expected}"
    except Exception as e:
        return False, f"Comparison error: {str(e)}"

def test_api_parser():
    """
    Test the /parse endpoint of the API by sending test cases and verifying the responses.
    This ensures the API correctly parses LaTeX expressions and returns the expected evaluations.
    """
    print(f"\n{Fore.CYAN}{'='*20} TESTING PARSER API {'='*20}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Testing API parse endpoint at: {PARSE_ENDPOINT}{Style.RESET_ALL}")
    
    all_pass = True
    failed_cases = []
    results = []
    total_time = 0

    for i, test_case in enumerate(test_data):
        test_num = i + 1
        solution_str = test_case.solution_string
        parameter_str = test_case.parameter_string
        expected_evaluation = test_case.expected_evaluation

        # Print test case info
        print(f"\n{Fore.CYAN}Test #{test_num}: {test_case.description}{Style.RESET_ALL}")
        
        # Prepare request data
        request_data = {
            "input": solution_str,
            "parameters": parameter_str
        }

        # Record start time for performance measurement
        start_time = time.time()
        success = False
        
        try:
            # Send request to API
            print(f"  {Fore.BLUE}⏳ Sending request to API...{Style.RESET_ALL}")
            response = requests.post(PARSE_ENDPOINT, json=request_data)
            
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            total_time += elapsed_time
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse response JSON
            result = response.json()
            
            # Verify success flag
            if not result.get('success', False):
                error_msg = result.get('error_message', 'No error message')
                print(f"  {Fore.RED}✗ API reported failure: {error_msg}{Style.RESET_ALL}")
                all_pass = False
                failed_cases.append(i)
                results.append({"id": i, "success": False, "pass": False, "time": elapsed_time})
                continue
                
            # Verify evaluation results exist
            if 'evaluation_results' not in result:
                print(f"  {Fore.RED}✗ No evaluation_results in API response{Style.RESET_ALL}")
                all_pass = False
                failed_cases.append(i)
                results.append({"id": i, "success": False, "pass": False, "time": elapsed_time})
                continue
                
            success = True
                
            # Get evaluation results
            api_evaluation = result['evaluation_results']
            
            # Compare with expected results
            is_equal, error_message = compare_results(api_evaluation, expected_evaluation)
            
            if is_equal:
                print(f"  {Fore.GREEN}✓ Test passed ({elapsed_time:.2f}s){Style.RESET_ALL}")
                results.append({"id": i, "success": True, "pass": True, "time": elapsed_time})
            else:
                print(f"  {Fore.RED}✗ Test failed: {error_message}{Style.RESET_ALL}")
                print(f"    {Fore.YELLOW}Expected: {expected_evaluation}{Style.RESET_ALL}")
                print(f"    {Fore.YELLOW}Actual:   {api_evaluation}{Style.RESET_ALL}")
                all_pass = False
                failed_cases.append(i)
                results.append({"id": i, "success": True, "pass": False, "time": elapsed_time})
                
        except requests.RequestException as e:
            elapsed_time = time.time() - start_time
            total_time += elapsed_time
            print(f"  {Fore.RED}✗ API request failed: {str(e)} ({elapsed_time:.2f}s){Style.RESET_ALL}")
            all_pass = False
            failed_cases.append(i)
            results.append({"id": i, "success": False, "pass": False, "time": elapsed_time})
        except Exception as e:
            elapsed_time = time.time() - start_time
            total_time += elapsed_time
            print(f"  {Fore.RED}✗ Test error: {str(e)} ({elapsed_time:.2f}s){Style.RESET_ALL}")
            all_pass = False
            failed_cases.append(i)
            results.append({"id": i, "success": False, "pass": False, "time": elapsed_time})

    # Print summary
    print(f"\n{Fore.CYAN}{'='*20} TEST SUMMARY {'='*20}{Style.RESET_ALL}")
    success_count = sum(1 for r in results if r["success"])
    pass_count = sum(1 for r in results if r["pass"])
    
    print(f"{Fore.CYAN}Total tests:{Style.RESET_ALL} {len(test_data)}")
    print(f"{Fore.CYAN}Successful API calls:{Style.RESET_ALL} {Fore.GREEN if success_count == len(test_data) else Fore.RED}{success_count}/{len(test_data)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Tests passed:{Style.RESET_ALL} {Fore.GREEN if pass_count == len(test_data) else Fore.RED}{pass_count}/{len(test_data)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Total time:{Style.RESET_ALL} {total_time:.2f}s")
    
    if not all_pass:
        print(f"\n{Fore.RED}Failed test cases:{Style.RESET_ALL}")
        for i in failed_cases:
            print(f"  {Fore.RED}• Test #{i+1}: {test_data[i].description}{Style.RESET_ALL}")
    
    # Calculate and display performance statistics
    if results:
        avg_time = sum(r["time"] for r in results) / len(results)
        max_time = max(r["time"] for r in results)
        max_time_id = next(r["id"] for r in results if r["time"] == max_time)
        
        print(f"\n{Fore.CYAN}Performance:{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}Average response time:{Style.RESET_ALL} {avg_time:.2f}s")
        print(f"  {Fore.CYAN}Slowest test:{Style.RESET_ALL} Test #{max_time_id+1} ({max_time:.2f}s) - {test_data[max_time_id].description}")
    
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
        success = test_api_parser()
        if success:
            print(f"\n{Fore.GREEN}{'='*20} ALL TESTS PASSED {'='*20}{Style.RESET_ALL}")
            sys.exit(0)
        else:
            print(f"\n{Fore.RED}{'='*20} SOME TESTS FAILED {'='*20}{Style.RESET_ALL}")
            sys.exit(1)
    else:
        print(f"\n{Fore.RED}Skipping tests because the API is not running.{Style.RESET_ALL}")
        print(f"Make sure the API is running at {API_BASE_URL}")
        sys.exit(1) 