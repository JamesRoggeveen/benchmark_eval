#!/usr/bin/env python3
"""
Test script for the /query endpoint of the API.
This test sends queries to different models and verifies the responses.
"""

import os
import sys
import requests
import time
import json
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# API endpoint configuration
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8080')
QUERY_ENDPOINT = f"{API_BASE_URL}/query"

def display_response(result, elapsed_time):
    """
    Display the API response in a formatted way.
    
    Args:
        result (dict): The API response JSON
        elapsed_time (float): Time taken for the request
    """
    print(f"\n{Fore.CYAN}{'='*20} RESPONSE {'='*20}{Style.RESET_ALL}")
    
    # Display basic response info
    print(f"{Fore.CYAN}Response Time:{Style.RESET_ALL} {elapsed_time:.2f}s")
    print(f"{Fore.CYAN}Success:{Style.RESET_ALL} {Fore.GREEN if result.get('success') else Fore.RED}{result.get('success', False)}{Style.RESET_ALL}")
    
    # Display the main response
    if 'response' in result:
        print(f"\n{Fore.CYAN}Response Content:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{result['response']}{Style.RESET_ALL}")
    
    # Display any metadata
    if 'metadata' in result:
        print(f"\n{Fore.CYAN}Metadata:{Style.RESET_ALL}")
        for key, value in result['metadata'].items():
            print(f"  {Fore.CYAN}{key}:{Style.RESET_ALL} {value}")
    
    # Display any error information
    if not result.get('success'):
        print(f"\n{Fore.RED}Error Information:{Style.RESET_ALL}")
        if 'error' in result:
            print(f"  {Fore.RED}Error:{Style.RESET_ALL} {result['error']}")
        if 'error_details' in result:
            print(f"  {Fore.RED}Details:{Style.RESET_ALL}")
            print(json.dumps(result['error_details'], indent=2))
    
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}\n")

def test_api_query():
    """
    Test the /query endpoint of the API by sending queries to different models.
    """
    print(f"\n{Fore.CYAN}{'='*20} TESTING QUERY API {'='*20}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Testing API query endpoint at: {QUERY_ENDPOINT}{Style.RESET_ALL}")
    
    # Test cases with different models
    test_cases = [
        {
            "model": "Gemini 2.0 Flash",
            "prompt": "What is 2 + 2? Please provide only the numerical answer.",
            "description": "Simple math problem with Gemini 2.0 Flash"
        },
        {
            "model": "GPT-4o-mini",
            "prompt": "What is 2 + 2? Please provide only the numerical answer.",
            "description": "Simple math problem with GPT-4o-mini"
        }
    ]
    
    all_pass = True
    failed_cases = []
    results = []
    total_time = 0

    for i, test_case in enumerate(test_cases):
        test_num = i + 1
        model = test_case["model"]
        prompt = test_case["prompt"]
        description = test_case["description"]

        # Print test case info
        print(f"\n{Fore.CYAN}Test #{test_num}: {description}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Model:{Style.RESET_ALL} {model}")
        print(f"{Fore.CYAN}Prompt:{Style.RESET_ALL} {prompt}")
        
        # Prepare request data
        request_data = {
            "prompt": prompt,
            "model": model
        }

        # Record start time for performance measurement
        start_time = time.time()
        success = False
        
        try:
            # Send request to API
            print(f"  {Fore.BLUE}⏳ Sending request to API...{Style.RESET_ALL}")
            response = requests.post(QUERY_ENDPOINT, json=request_data)
            
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            total_time += elapsed_time
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse response JSON
            result = response.json()
            
            # Display the response
            display_response(result, elapsed_time)
            
            # Verify success flag
            if not result.get('success', False):
                error_msg = result.get('error', 'No error message')
                print(f"  {Fore.RED}✗ API reported failure: {error_msg}{Style.RESET_ALL}")
                all_pass = False
                failed_cases.append(i)
                results.append({"id": i, "success": False, "pass": False, "time": elapsed_time})
                continue
                
            # Verify response exists
            if 'response' not in result:
                print(f"  {Fore.RED}✗ No response in API response{Style.RESET_ALL}")
                all_pass = False
                failed_cases.append(i)
                results.append({"id": i, "success": False, "pass": False, "time": elapsed_time})
                continue
                
            success = True
            results.append({"id": i, "success": True, "pass": True, "time": elapsed_time})
                
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
    
    print(f"{Fore.CYAN}Total tests:{Style.RESET_ALL} {len(test_cases)}")
    print(f"{Fore.CYAN}Successful API calls:{Style.RESET_ALL} {Fore.GREEN if success_count == len(test_cases) else Fore.RED}{success_count}/{len(test_cases)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Tests passed:{Style.RESET_ALL} {Fore.GREEN if pass_count == len(test_cases) else Fore.RED}{pass_count}/{len(test_cases)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Total time:{Style.RESET_ALL} {total_time:.2f}s")
    
    if not all_pass:
        print(f"\n{Fore.RED}Failed test cases:{Style.RESET_ALL}")
        for i in failed_cases:
            print(f"  {Fore.RED}• Test #{i+1}: {test_cases[i]['description']}{Style.RESET_ALL}")
    
    # Calculate and display performance statistics
    if results:
        avg_time = sum(r["time"] for r in results) / len(results)
        max_time = max(r["time"] for r in results)
        max_time_id = next(r["id"] for r in results if r["time"] == max_time)
        
        print(f"\n{Fore.CYAN}Performance:{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}Average response time:{Style.RESET_ALL} {avg_time:.2f}s")
        print(f"  {Fore.CYAN}Slowest test:{Style.RESET_ALL} Test #{max_time_id+1} ({max_time:.2f}s) - {test_cases[max_time_id]['description']}")
    
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
        success = test_api_query()
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