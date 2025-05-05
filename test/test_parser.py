import os
import sys
import numpy as np
import time
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Now import from src
from src.parser import evaluate_solution, ParsingResult
from test_data.test_parser_data import test_data, TestParserData

def is_complex_or_float(val):
    """Check if value is complex or can be converted to float"""
    if isinstance(val, complex):
        return True
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False

def compare_results(actual_results, expected_results):
    """
    Compare actual results with expected results, handling complex numbers.
    
    Returns:
        tuple: (is_equal, error_message)
    """
    if len(actual_results) != len(expected_results):
        return False, f"Result length mismatch: got {len(actual_results)}, expected {len(expected_results)}"
    
    try:
        # Handle numeric comparison with numpy for precision and complex numbers
        if all(is_complex_or_float(val) for val in actual_results + expected_results):
            return np.allclose(actual_results, expected_results), ""
        else:
            # If not all values are numeric, compare directly
            is_equal = actual_results == expected_results
            return is_equal, "" if is_equal else f"Values differ: {actual_results} vs {expected_results}"
    except Exception as e:
        # Include the actual expression in the error message
        return False, f"Comparison error: {str(e)}\nExpression: {actual_results}"

def test_parser():
    print(f"\n{Fore.CYAN}{'='*20} TESTING PARSER {'='*20}{Style.RESET_ALL}")
    
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

        # Record start time for performance measurement
        start_time = time.time()
        
        try:
            # Run the test
            print(f"  {Fore.BLUE}⏳ Evaluating expression...{Style.RESET_ALL}")
            result = evaluate_solution(solution_str, parameter_str)
            
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            total_time += elapsed_time
            
            if not result.success:
                print(f"  {Fore.RED}✗ Parsing failed: {result.error_message} ({elapsed_time:.2f}s){Style.RESET_ALL}")
                print(f"    {Fore.YELLOW}Solution: {solution_str}{Style.RESET_ALL}")
                print(f"    {Fore.YELLOW}Parameters: {parameter_str}{Style.RESET_ALL}")
                if hasattr(result, 'intermediate_expressions'):
                    print(f"    {Fore.BLUE}Intermediate expressions: {result.intermediate_expressions}{Style.RESET_ALL}")
                if hasattr(result, 'parameter_dict'):
                    print(f"    {Fore.BLUE}Parameter dict: {result.parameter_dict}{Style.RESET_ALL}")
                failed_cases.append(i)
                all_pass = False
                results.append({"id": i, "success": False, "pass": False, "time": elapsed_time})
                continue
                
            # Compare with expected results
            is_equal, error_message = compare_results(result.evaluation_results, expected_evaluation)
            
            # Format parameter values for display
            param_display = {}
            if result.parameter_values:
                for key, value in result.parameter_values.items():
                    param_display[str(key)] = value
            
            if is_equal:
                print(f"  {Fore.GREEN}✓ Test passed ({elapsed_time:.2f}s){Style.RESET_ALL}")
                print(f"    {Fore.BLUE}• Original: {solution_str}{Style.RESET_ALL}")
                print(f"    {Fore.BLUE}• Parsed: {result.intermediate_expressions}{Style.RESET_ALL}")
                print(f"    {Fore.BLUE}• Parameters: {param_display}{Style.RESET_ALL}")
                print(f"    {Fore.BLUE}• Result: {result.evaluation_results}{Style.RESET_ALL}")
                results.append({"id": i, "success": True, "pass": True, "time": elapsed_time})
            else:
                print(f"  {Fore.RED}✗ Test failed: {error_message} ({elapsed_time:.2f}s){Style.RESET_ALL}")
                print(f"    {Fore.YELLOW}Expected: {expected_evaluation}{Style.RESET_ALL}")
                print(f"    {Fore.YELLOW}Actual:   {result.evaluation_results}{Style.RESET_ALL}")
                print(f"    {Fore.BLUE}Original: {solution_str}{Style.RESET_ALL}")
                print(f"    {Fore.BLUE}Intermediate expressions: {result.intermediate_expressions}{Style.RESET_ALL}")
                print(f"    {Fore.BLUE}Parameters: {param_display}{Style.RESET_ALL}")
                if hasattr(result, 'parameter_dict'):
                    print(f"    {Fore.BLUE}Parameter dict: {result.parameter_dict}{Style.RESET_ALL}")
                if hasattr(result, 'sympy_expressions'):
                    print(f"    {Fore.BLUE}SymPy expressions: {result.sympy_expressions}{Style.RESET_ALL}")
                failed_cases.append(i)
                all_pass = False
                results.append({"id": i, "success": True, "pass": False, "time": elapsed_time})
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            total_time += elapsed_time
            print(f"  {Fore.RED}✗ Exception: {str(e)} ({elapsed_time:.2f}s){Style.RESET_ALL}")
            print(f"    {Fore.YELLOW}Solution: {solution_str}{Style.RESET_ALL}")
            print(f"    {Fore.YELLOW}Parameters: {parameter_str}{Style.RESET_ALL}")
            if hasattr(result, 'intermediate_expressions'):
                print(f"    {Fore.BLUE}Intermediate expressions: {result.intermediate_expressions}{Style.RESET_ALL}")
            if hasattr(result, 'parameter_dict'):
                print(f"    {Fore.BLUE}Parameter dict: {result.parameter_dict}{Style.RESET_ALL}")
            if hasattr(result, 'sympy_expressions'):
                print(f"    {Fore.BLUE}SymPy expressions: {result.sympy_expressions}{Style.RESET_ALL}")
            failed_cases.append(i)
            all_pass = False
            results.append({"id": i, "success": False, "pass": False, "time": elapsed_time})
    
    # Print summary
    print(f"\n{Fore.CYAN}{'='*20} TEST SUMMARY {'='*20}{Style.RESET_ALL}")
    success_count = sum(1 for r in results if r["success"])
    pass_count = sum(1 for r in results if r["pass"])
    
    print(f"{Fore.CYAN}Total tests:{Style.RESET_ALL} {len(test_data)}")
    print(f"{Fore.CYAN}Successful parsing:{Style.RESET_ALL} {Fore.GREEN if success_count == len(test_data) else Fore.RED}{success_count}/{len(test_data)}{Style.RESET_ALL}")
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
    
    if all_pass:
        print(f"\n{Fore.GREEN}{'='*20} ALL TESTS PASSED {'='*20}{Style.RESET_ALL}")
        return 0
    else:
        print(f"\n{Fore.RED}{'='*20} SOME TESTS FAILED {'='*20}{Style.RESET_ALL}")
        return 1

if __name__ == "__main__":
    exit_code = test_parser()
    sys.exit(exit_code)