import os
import sys
import numpy as np

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Now import from src
from src.parser import evaluate_solution, ParsingResult
from test_data.test_parser_data import test_data, TestParserData

def test_parser():
    all_pass = True
    failed_cases = []
    for i, test_case in enumerate(test_data):
        solution_str = test_case.solution_string
        parameter_str = test_case.parameter_string
        expected_evaluation = test_case.expected_evaluation

        try:
            result = evaluate_solution(solution_str, parameter_str)
            assert result.success, f"Failed to parse solution: {result.error_message}"
            
            # Handle potential complex numbers in results
            assert np.allclose(result.evaluation_results, expected_evaluation), f"Evaluation results do not match expected values"
            print(f"Test case {test_case.description} passed")
        except Exception as e:
            print(f"Test case {test_case.description} failed: {str(e)}")
            failed_cases.append(i)
    if all_pass:
        print("All test cases passed")
    else:
        print(f"Test cases {failed_cases} failed")

if __name__ == "__main__":
    test_parser()