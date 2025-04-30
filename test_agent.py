import csv
import json
import re
import os
import datetime
import pandas as pd
from typing import List, Dict, Any, Tuple, Set
from core.agent import process_user_query
from dotenv import load_dotenv
import time
# Load environment variables
load_dotenv()

def read_test_cases(csv_file_path: str) -> List[Dict[str, str]]:
    """
    Read test cases from CSV file.
    
    Args:
        csv_file_path (str): Path to CSV file containing test cases
        
    Returns:
        List[Dict[str, str]]: List of test cases with query and expected tools
    """
    test_cases = []
    
    try:
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                test_cases.append({
                    'query': row['query'],
                    'expected_tools': row['expected_tools']
                })
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return []
        
    return test_cases

def parse_expected_tools(expected_tools_str: str) -> Set[str]:
    """
    Parse the expected tools string from CSV into a set of tool names.
    
    Args:
        expected_tools_str (str): Comma-separated string of expected tool names
        
    Returns:
        Set[str]: Set of expected tool names
    """
    # Handle empty strings
    if not expected_tools_str or expected_tools_str.strip() == '':
        return set()
    
    # Split by comma and strip whitespace for each tool name
    return {tool.strip() for tool in expected_tools_str.split(',') if tool.strip()}

from typing import List, Dict, Any, Set

def get_actual_tools(results: List[Dict[str, Any]]) -> Set[str]:
    """
    Extract all tool names used from the test results, handling various nested structures.
    
    Args:
        results (List[Dict[str, Any]]): List of task results from agent
        
    Returns:
        Set[str]: Set of all tool names used
    """
    tool_names = set()
    
    def extract_tool_names(item: Any) -> None:
        """Recursively extract tool names from nested dictionaries and lists."""
        if isinstance(item, dict):
            # Extract tool_name if it exists at this level
            if 'tool_name' in item:
                tool_names.add(item['tool_name'])
            
            # Check for tools or calls fields that might contain tool information
            if 'tools' in item and isinstance(item['tools'], list):
                for tool in item['tools']:
                    extract_tool_names(tool)
            
            if 'tool_calls' in item and isinstance(item['tool_calls'], list):
                for call in item['tool_calls']:
                    extract_tool_names(call)
                    
            # Recursively process all other dictionary values
            for value in item.values():
                extract_tool_names(value)
                
        elif isinstance(item, list):
            # Process each item in the list
            for element in item:
                extract_tool_names(element)
    
    # Process all results
    for result in results:
        extract_tool_names(result)
        
    return tool_names

def evaluate_test_case(query: str, expected_tools_set: Set[str]) -> Tuple[List[Dict[str, Any]], str, bool, Set[str], Set[str], Set[str]]:
    """
    Run a test case and evaluate the results.
    
    Args:
        query (str): The query to test
        expected_tools_set (Set[str]): Set of expected tool names
        
    Returns:
        Tuple containing:
        - results (List[Dict]): Raw results from agent
        - final_answer (str): Final answer from agent
        - passed (bool): Whether all expected tools were used
        - actual_tools_set (Set[str]): Set of actual tool names used
        - missing_tools (Set[str]): Expected tools that weren't used
        - extra_tools (Set[str]): Unexpected tools that were used
    """
    try:
        results, final_answer = process_user_query(query)
        print("Processing completed with tools:", [r.get('tool_name', 'unknown') for r in results])
        
        actual_tools_set = get_actual_tools(results)
        missing_tools = expected_tools_set - actual_tools_set
        extra_tools = actual_tools_set - expected_tools_set
        
        # missing_tools, extra_tools = compare_word_lists(expected_tools_set, actual_tools_set)
        
        # Test passes if all expected tools were used (we don't care about extras)
        passed = len(missing_tools) == 0
        
        return results, final_answer, passed, actual_tools_set, missing_tools, extra_tools
    
    except Exception as e:
        print(f"Error processing query '{query}': {str(e)}")
        return [], str(e), False, set(), expected_tools_set, set()

def run_tests(csv_file_path: str, output_csv_path: str = None) -> Tuple[int, int, List[Dict[str, Any]]]:
    """
    Run all test cases from the CSV file and generate results.
    
    Args:
        csv_file_path (str): Path to CSV file with test cases
        output_csv_path (str, optional): Path to save detailed results CSV. If None, uses timestamp.
        
    Returns:
        Tuple containing:
        - total_tests (int): Total number of tests run
        - passed_tests (int): Number of tests that passed
        - detailed_results (List[Dict]): Detailed results for each test case
    """
    test_cases = read_test_cases(csv_file_path)
    total_tests = len(test_cases)
    passed_tests = 0
    detailed_results = []
    
    print(f"\n{'=' * 80}")
    print(f"Running {total_tests} test cases from {csv_file_path}")
    print(f"{'=' * 80}")
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case['query']
        expected_tools_str = test_case['expected_tools']
        expected_tools_set = parse_expected_tools(expected_tools_str)
        
        print(f"\nTest {i}/{total_tests}: {query}")
        print(f"Expected tools: {', '.join(expected_tools_set)}")
        
        results, final_answer, passed, actual_tools_set, missing_tools, extra_tools = evaluate_test_case(query, expected_tools_set)
        time.sleep(5)
        
        if passed:
            passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        print(f"Status: {status}")
        print(f"Actual tools: {', '.join(actual_tools_set)}")
        
        if missing_tools:
            print(f"Missing tools: {', '.join(missing_tools)}")
        if extra_tools:
            print(f"Extra tools: {', '.join(extra_tools)}")
        
        # Prepare detailed results
        result_entry = {
            'query': query,
            'expected_tools': expected_tools_str,
            'actual_tools': ','.join(actual_tools_set),
            'passed': passed,
            'missing_tools': ','.join(missing_tools) if missing_tools else '',
            'extra_tools': ','.join(extra_tools) if extra_tools else '',
            'final_answer': final_answer[:200] + '...' if len(final_answer) > 200 else final_answer,
            'raw_results': str(results)[:300] + '...' if len(str(results)) > 300 else str(results)
        }
        
        detailed_results.append(result_entry)
    
    # Generate summary
    print(f"\n{'=' * 80}")
    print(f"Test Summary: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
    print(f"{'=' * 80}")
    
    # Save detailed results to CSV
    if output_csv_path is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_csv_path = f"test/test_results_{timestamp}.csv"
    
    try:
        # Convert to DataFrame and save
        df = pd.DataFrame(detailed_results)
        df.to_csv(output_csv_path, index=False)
        print(f"\nDetailed test results saved to: {output_csv_path}")
    except Exception as e:
        print(f"Error saving results to CSV: {str(e)}")
    
    return total_tests, passed_tests, detailed_results

def main():
    """Main function to run the tests"""
    # Default input and output file paths
    default_input_csv = "test/test_cases.csv"
    
    # Allow command line arguments to override defaults
    import argparse
    parser = argparse.ArgumentParser(description='Run tests for Gyanova agent system')
    parser.add_argument('--input', type=str, default=default_input_csv, 
                        help=f'Path to input CSV file with test cases (default: {default_input_csv})')
    parser.add_argument('--output', type=str, default=None,
                        help='Path to output CSV file for results (default: test_results_TIMESTAMP.csv)')
    
    args = parser.parse_args()
    
    # Run tests
    run_tests(args.input, args.output)

if __name__ == "__main__":
    main()