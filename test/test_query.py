import os
import sys
import numpy as np
import time
from colorama import Fore, Style, init
from dotenv import load_dotenv
load_dotenv()

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Now import from src
from src.evaluator import SUPPORTED_MODELS, SUPPORTED_MODELS_GEMINI, SUPPORTED_MODELS_OPENAI, query_llm
from test_data.test_parser_data import test_data, TestParserData

def test_query_llm(query, model):
    response, error = query_llm(query, model)
    print(response)
    if error:
        print(f"{Fore.RED}Error: {error}{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}No error{Style.RESET_ALL}")


if __name__ == "__main__":
    model = "GPT-4o-mini"
    query = "What is 2 + 2?"
    test_query_llm(query, model)
