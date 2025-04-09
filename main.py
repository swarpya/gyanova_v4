from core.agent import process_user_query

def main():
    user_query = "give detailed resignation letter from software engineering job employee and send that to swaroopingavale73@gmail.com"
    
    print("User Query:", user_query)
    results, final_answer = process_user_query(user_query)
    
    print("\n--- Results from Each Tool ---")
    for result in results:
        print(f"Task {result['task_number']}: {result['tool_name']}")
        print(f"Parameters: {result['parameters']}")
        print(f"Result: {str(result['result'])[:150]}..." if len(str(result['result'])) > 150 else result['result'])
        print()
    
    print("\n--- Final Answer ---")
    print(final_answer)

if __name__ == "__main__":
    main()