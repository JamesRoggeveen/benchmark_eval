import os
import sys
import time
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Now import from src
from src.evaluator import compare_latex_expressions
from test_data.test_parser_func_data import test_data

def test_parser_func():
    print(f"\n{Fore.CYAN}{'='*20} TESTING PARSER FUNCTION COMPARISON {'='*20}{Style.RESET_ALL}")
    
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
        expected_result = test_case.expected_result
        description = test_case.description or "No description provided"

        # Print test case info
        print(f"\n{Fore.CYAN}Test #{test_num}: {description}{Style.RESET_ALL}")

        # Record start time for performance measurement
        start_time = time.time()
        
        try:
            # Run the test
            print(f"  {Fore.BLUE}⏳ Comparing expressions...{Style.RESET_ALL}")
            result = compare_latex_expressions(comparison_str, solution_str, parameter_str, function_str)
            
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            total_time += elapsed_time

            # Print the parsed expressions if parsing was successful
            if result.model_result and result.model_result.sympy_expressions:
                print(f"    {Fore.BLUE}• Model expressions: {[str(expr) for expr in result.model_result.sympy_expressions]}{Style.RESET_ALL}")
            
            if result.solution_result and result.solution_result.sympy_expressions:
                print(f"    {Fore.BLUE}• Solution expressions: {[str(expr) for expr in result.solution_result.sympy_expressions]}{Style.RESET_ALL}")
            
            # Check if the actual result matches the expected result
            if result.is_equivalent == expected_result:
                print(f"  {Fore.GREEN}✓ Test passed ({elapsed_time:.2f}s){Style.RESET_ALL}")
                print(f"    {Fore.BLUE}• Expected result: {expected_result}{Style.RESET_ALL}")
                print(f"    {Fore.BLUE}• Actual result: {result.is_equivalent}{Style.RESET_ALL}")
                results.append({"id": i, "success": True, "pass": True, "time": elapsed_time})
            else:
                print(f"  {Fore.RED}✗ Test failed ({elapsed_time:.2f}s){Style.RESET_ALL}")
                print(f"    {Fore.YELLOW}• Expected result: {expected_result}{Style.RESET_ALL}")
                print(f"    {Fore.YELLOW}• Actual result: {result.is_equivalent}{Style.RESET_ALL}")
                if result.error_message:
                    print(f"    {Fore.YELLOW}• Error: {result.error_message}{Style.RESET_ALL}")
                failed_cases.append(i)
                all_pass = False
                results.append({"id": i, "success": False, "pass": False, "time": elapsed_time})
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            total_time += elapsed_time
            print(f"  {Fore.RED}✗ Exception: {str(e)} ({elapsed_time:.2f}s){Style.RESET_ALL}")
            failed_cases.append(i)
            all_pass = False
            results.append({"id": i, "success": False, "pass": False, "time": elapsed_time})
    
    # Print summary
    print(f"\n{Fore.CYAN}{'='*20} TEST SUMMARY {'='*20}{Style.RESET_ALL}")
    success_count = sum(1 for r in results if r["success"])
    pass_count = sum(1 for r in results if r["pass"])
    
    print(f"{Fore.CYAN}Total tests:{Style.RESET_ALL} {len(test_data)}")
    print(f"{Fore.CYAN}Successful comparisons:{Style.RESET_ALL} {Fore.GREEN if success_count == len(test_data) else Fore.RED}{success_count}/{len(test_data)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Tests passed:{Style.RESET_ALL} {Fore.GREEN if pass_count == len(test_data) else Fore.RED}{pass_count}/{len(test_data)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Total time:{Style.RESET_ALL} {total_time:.2f}s")
    
    if not all_pass:
        print(f"\n{Fore.RED}Failed test cases:{Style.RESET_ALL}")
        for i in failed_cases:
            print(f"  {Fore.RED}• Test #{i+1}: {test_data[i].description or 'No description'}{Style.RESET_ALL}")
    
    # Calculate and display performance statistics
    if results:
        avg_time = sum(r["time"] for r in results) / len(results)
        max_time = max(r["time"] for r in results)
        max_time_id = next(r["id"] for r in results if r["time"] == max_time)
        
        print(f"\n{Fore.CYAN}Performance:{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}Average response time:{Style.RESET_ALL} {avg_time:.2f}s")
        print(f"  {Fore.CYAN}Slowest test:{Style.RESET_ALL} Test #{max_time_id+1} ({max_time:.2f}s) - {test_data[max_time_id].description or 'No description'}")
    
    if all_pass:
        print(f"\n{Fore.GREEN}{'='*20} ALL TESTS PASSED {'='*20}{Style.RESET_ALL}")
        return 0
    else:
        print(f"\n{Fore.RED}{'='*20} SOME TESTS FAILED {'='*20}{Style.RESET_ALL}")
        return 1

if __name__ == "__main__":
    exit_code = test_parser_func()
    sys.exit(exit_code) 