import re

def extract_boxed_equations(text):
    box_pattern = r'\\boxed\{(.*)\}'  # Use greedy matching
    box_matches = re.findall(box_pattern, text, re.DOTALL)
    if len(box_matches) == 0:
        raise ValueError("No boxed equations found in the text.")
    elif len(box_matches) > 1:
        raise ValueError("Multiple boxed equations found in the text.")
    return box_matches[0].strip()  

def post_processing(text):
    text = replace_bracket(text)
    return text

def replace_bracket(text):
    return text.replace(r'\{','{').replace(r'\}','}')


def isequal_numerics(LLM_output, ground_truth):
    """
    Compare the LLM output with the ground truth.
    """
    # Extract the boxed equation from the LLM output
    try:
        LLM_output = extract_boxed_equations(LLM_output)
    except ValueError as e:
        raise ValueError(f"Failed to extract boxed equations: {LLM_output}") from e

    # post_process the LLM output
    try:
        LLM_output = post_processing(LLM_output)
    except ValueError:
        raise ValueError("Error in post-processing LLM's output.") from e
    
    # eval the LLM output
    try:
        LLM_output = eval(LLM_output)
    except Exception as e:
        raise ValueError(f"Error in evaluating LLM's output: {e}")
        return False

    # eval the ground truth
    try:
        ground_truth = eval(ground_truth)
    except Exception as e:
        raise ValueError(f"Error in evaluating ground truth: {e}")


    try:
        if LLM_output == ground_truth:
            return True
    except Exception:
        pass

    try:
        if set([LLM_output]) == ground_truth:
            return True
    except Exception:
        pass

    try:
        if set(LLM_output) == ground_truth:
            return True
    except Exception:
        pass

    return False