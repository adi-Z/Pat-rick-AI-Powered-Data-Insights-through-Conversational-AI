import re
import datetime
import timeit
import csv  # Add this import
from sqlalchemy import create_engine, text
from langchain_community.llms import Ollama

# Initialize Ollama model
llm = Ollama(model="mistral")  # Ensure this is the correct model identifier

# Database connection setup for PostgreSQL
postgresql_connection_string = 'postgresql://{username}:{password}@{hostname}:{port}/{dbname}'
engine = create_engine(
    postgresql_connection_string.format(
        username="postgres",  # Replace with your actual username
        password="197346",  # Replace with your actual password
        hostname="localhost",
        port="5432",  # Default PostgreSQL port
        dbname="postgres"  # Replace with your actual database name
)
)

# Data dictionary for the CANADAPOST table ??
data_dictionary = {
    "FYFW": {"description": "Fiscal year Fiscal Week", "type": "text"},
    "Origin_Date": {"description": "The day when the item was first received by Canada post within that FYFW", "type": "date"},
    "FAIL": {"description": "T if the Items failed F if it did not fail", "type": "text"},
    "CUSTOMER_NAME": {"description": "Name of the commercial Customer", "type": "text"},
    "ORIGIN_REGION": {"description": "Five regions: Pacific, GTA, Atlantic, Ontario, Quebec, Prairie", "type": "text"},
    "LINKS": {"description": "The link to be delivered like Toronto >> Toronto", "type": "text"},
    "DESTINATION_REGION": {"description": "Five regions: Pacific, GTA, Atlantic, Ontario, Quebec, Prairie", "type": "text"},
    "WORK_CENTER_NAME": {"description": "The name of the sorters where the items got scanned", "type": "text"},
    "FAILURE_CATEGORY": {"description": "The category in which the item failed in the entire process", "type": "text"},
    "STREAM": {"description": "3 streams: STREAM 1, STREAM 2, STREAM 3", "type": "text"},
    "DP0_VOL": {"description": "How many items failed on that link, for that customer, on that particular date.", "type": "integer"}
}


def run_query(query):
    """Execute the SQL query and return results, with caching."""
    with engine.connect() as connection:
        result = connection.execute(text(query))
        rows = result.fetchall()
        return rows


def extract_sql_query(model_response):
    """Extract SQL query from the model's response."""
    # Attempt to find SQL query within the model's response
    match = re.search(r"```(?:sql|vbnet)\n(.*?);?\n```", model_response, re.IGNORECASE | re.DOTALL)


    if match:
        return match.group(1).strip()  # Return the matched SQL query content
    else:
        print("SQL query not found in the model's response.")
        return None

def generate_sql_query(nl_query):
    # Format the data dictionary into a string to include in the prompt
    data_dict_str = "\n".join([f"{key}: {value}" for key, value in data_dictionary.items()])
    
    # Include example rows for context
    example_rows = """
    | FYFW | Origin_Date | FAIL | CUSTOMER_NAME  | ORIGIN_REGION | LINKS                    | DESTINATION_REGION | WORK_CENTER_NAME            | FAILURE_CATEGORY                               | STREAM | DP0_VOL |
    |------|-------------|------|----------------|---------------|-------------------------|--------------------|----------------------------|------------------------------------------------|--------|---------|
    | 202330 | 2023-07-28 | T    | SECOND BIND    | GTA           | Toronto >> Toronto      | GTA                | WILLOWDALE STN D           | Depot Miss Cut-off (DSS After 11)              | Stream 3| 1       |
    | 202330 | 2023-07-24 | T    | ROUTINE        | Prairie       | Calgary >> Thompson     | Prairie            | WINNIPEG / SHIPPING SORTER | Processed at destination plant after 12pm      | Stream 2| 1       |
    | 202330 | 2023-07-26 | T    | PRODIGY PARTS  | GTA           | Toronto >> Winnipeg     | Prairie            | WINNIPEG / SHIPPING SORTER | Processed after destination plant cut-off prior| Stream 2| 1       |
    """
    
    # Add a category
    instruction_for_category = "Mostly is the format for failure category like this: the [category name] category"
    
    # Add a focused instruction for considering the LINK column
    instruction_for_link ="""
    When generating SQL queries based on the user's question, it's crucial to match the conditions exactly as specified. 
    For questions concerning specific links, such as "Toronto >> Toronto", you must use the 'LINKS' column directly in the 
    WHERE clause of the SQL query. Directly translate specific details from the question into the SQL query. 
    For instance, if the query mentions a specific link "Toronto >> Toronto", use WHERE LINKS = 'Toronto >> Toronto' in your SQL query.
    
    Ensure the query includes filtering for failures (where FAIL='T'). 
    Use SUM(DP0_VOL) to calculate total failures.
    """

    # Adding new instruction category matching
    instruction_for_failure_category = """
    Mostly is the format for failure category like this: the [category name] category. When considering the 'FAILURE_CATEGORY' in the WHERE clause, match the exact text from the query. 
    - If the query specifies a category without parentheses, like 'Origin Miss Cut-off', match exactly without adding details in parentheses.
    - Conversely, if the query includes details within parentheses, like 'Depot Miss Cut-off (DSS After 11)', include them in the match.
    Example:
    Query: Count failures in the 'Origin Miss Cut-off' category.
    Incorrect SQL WHERE clause: WHERE FAILURE_CATEGORY = 'Origin Miss Cut-off (DSS After 11)'
    Correct SQL WHERE clause: WHERE FAILURE_CATEGORY = 'Origin Miss Cut-off'    
    """

    #failure
    instruction_for_failure = "If there is 'failure' word in the user input, always put in WHERE statement FAIL='T'"
    
    # Incorporate a new instruction for generating a natural language summary
    instruction_for_natural_summary = """
    Additionally, provide a natural language summary of what the SQL query's results would imply. For example, if the query is expected to return the total volume of failed items, summarize this expectation in a sentence. Do not use SQL query result or CANADAPOST table in your sentences. Just give natural language summary.
    """
    
    #do not include nulls
    instruction_for_null = """Apply 'IS NOT NULL' only to text columns included in the SELECT statement. 
    This ensures queries exclude rows with missing text data, maintaining result accuracy. 
    If the SELECT contains only numbers, skip 'IS NOT NULL'. This rule is key for text data integrity."""

    # Dynamic example query based on the instruction
    specific_example_query = """
    Question: What are the top 10 customers by number of defects?
    SQL query:
    SELECT CUSTOMER_NAME, SUM(DP0_VOL) AS FAILURE_COUNT
    FROM CANADAPOST
    WHERE CUSTOMER_NAME IS NOT NULL -- example of handling null values AND FAIL='T'
    GROUP BY CUSTOMER_NAME
    ORDER BY FAILURE_COUNT DESC
    FETCH FIRST 10 ROWS ONLY
    """

    # Constructing the prompt with the added instruction, example rows, and the user's task
    prompt = f"""
    {instruction_for_link}
    {instruction_for_category}
    {instruction_for_failure_category}
    {instruction_for_failure}
    {instruction_for_null}
    {example_rows}
    
    Data Dictionary for CANADAPOST:
    {data_dict_str}

    Example:
    {specific_example_query}
    
    Task: Generate an SQL query for: "{nl_query}". Do not use spaces or underscores in aliases. 
    After generating the SQL query, provide a natural language summary explaining the implication of the query's results.
    {instruction_for_natural_summary}
    """

    response = llm.invoke(prompt)  # Invoke the model with the constructed prompt
    print(response)  # Debugging: print the model's full response for inspection

    sql_query = extract_sql_query(response)  # Extract the SQL query from the response
    if not sql_query:
        print("SQL query not found in the model's response.")
        return None
    
    return sql_query

def log_to_csv_file(question, sql_query, response):
    with open("chatbot_log.csv", "a", newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([timestamp, question, sql_query, response])

#terminal
def main():
    print("Welcome to the SQL Chatbot!")
    while True:
        user_input = input("Ask a question about the data in the CANADAPOST table (or type 'exit' to quit): ").strip()
        if user_input.lower() == 'exit':
            print("Exiting the chatbot. Goodbye!")
            break
        start_time = timeit.default_timer()  # Start timing
        try:
            sql_query = generate_sql_query(user_input)
            if sql_query:
                #print(f"Generated SQL Query: {sql_query}")  # For debugging
                results = run_query(sql_query)
                response = '\n'.join([str(row) for row in results]) or "No results found or query execution failed."
                print(response)
                # Log the interaction to CSV
                log_to_csv_file(user_input, sql_query, response)
            else:
                print("Failed to generate a SQL query.")
                # Log the failed attempt to generate SQL query
                log_to_csv_file(user_input, "No SQL query generated", "Failed to generate a SQL query.")
        except Exception as e:
            error_message = f"An error occurred: {e}"
            print(error_message)
            # Log the error
            log_to_csv_file(user_input, "Error in SQL query generation or execution", error_message)
        finally:
            end_time = timeit.default_timer()  # End timing
            print(f"Time taken: {end_time - start_time} seconds")  # Print the time taken

if __name__ == "__main__":
    main()