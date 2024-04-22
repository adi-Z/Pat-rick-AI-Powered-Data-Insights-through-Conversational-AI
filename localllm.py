import re
import datetime
import timeit
import csv  # Add this import
from sqlalchemy import create_engine, text
from langchain_community.llms import Ollama
from sqlalchemy.exc import ProgrammingError
import pandas as pd
import matplotlib.pyplot as plt
import warnings
import seaborn as sns
import matplotlib.pyplot as plt


# Initialize Ollama model
llm = Ollama(model="mistral")  # Ensure this is the correct model identifier

# Database connection setup for PostgreSQL
postgresql_connection_string = 'postgresql://{username}:{password}@{hostname}:{port}/{dbname}'
engine = create_engine(
    postgresql_connection_string.format(
        username="x",  # Replace with your actual username
        password="x",  # Replace with your actual password
        hostname="localhost",
        port="5432",  # Default PostgreSQL port
        dbname="postgres"  # Replace with your actual database name
)
)

# Data dictionary for the CANADAPOST table
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
    "DP0_VOL": {"description": "How many items failed on that link, for that customer, on that particular date. Count of failed items", "type": "integer"}
}



def validate_and_correct_query(sql_query):
    """
    Checks for common typographical errors in SQL query aliases and corrects them.
    """
    corrections = {
        "FAILEURE_COUNT": "FAILURE_COUNT", 
        "FAILE_CATEGORY": "FAILURE_CATEGORY",
        "FAILEDO_CATEGORY": "FAILURE_CATEGORY",
         "FAILEDE_CATEGORY": "FAILURE_CATEGORY" # Correcting a common typo
        # Add other common corrections here
    }

    for incorrect, correct in corrections.items():
        sql_query = sql_query.replace(incorrect, correct)

    return sql_query


def run_query(query):
    """Execute the SQL query and return results without 'None', with up to 2 retries on failure."""
    max_retries = 8
    attempts = 0
    
    while attempts <= max_retries:
        try:
            corrected_query = validate_and_correct_query(query)  # Validate and correct the query before execution
            with engine.connect() as connection:
                result = connection.execute(text(corrected_query))
                rows = result.fetchall()
                return rows  # If successful, return the rows
        except ProgrammingError as e:
            if attempts == max_retries:
                print(f"Final attempt failed with SQL execution error: {e}")
                return None  # Return None after the final attempt fails
            else:
                print(f"Attempt {attempts + 1} failed with SQL execution error: {e}, retrying...")
                attempts += 1
                # Optionally, add a delay here if you think it's necessary
                # time.sleep(1)  # Be sure to import 'time' at the top if you uncomment this




def extract_sql_query(model_response):
    # Remove common markdown elements and unnecessary characters
    adjusted_response = model_response.replace('```', '').replace('`', '').replace('[', '').replace(']', '').replace('{', '').replace('}', '')

    # Find the main SQL query
    match = re.search(r"SELECT .*?FROM canadapost.*?(?=;|$)", adjusted_response, re.IGNORECASE | re.DOTALL)
    if match:
        sql_query = match.group().strip()
        # Remove backslashes before underscores
        sql_query = sql_query.replace(r"\_", "_")

        # Now, search for commented filters and prepare to include them in the query
        # This pattern looks for commented-out filters
        filters = re.findall(r"-- AND (.+)", adjusted_response)
        if filters:
            # Assuming the WHERE clause exists and we just append AND conditions
            for filter_condition in filters:
                sql_query += f" AND {filter_condition}"

        print("Extracted SQL Query:", sql_query)
        return sql_query
    else:
        print("Debug: Adjusted SQL query not found. Inspected content:", adjusted_response[:500])
        return None


def python_parse(llm_response):
    # Adjusting the pattern to explicitly capture the 'python' identifier and ensure we grab the entire code block
    pattern = r"```python\n([\s\S]*?)\n```"
    matches = re.findall(pattern, llm_response)

    if matches:
        # Assuming there's only one match; otherwise, you might need to handle multiple blocks
        extracted_code = matches[0]
    else:
        # If no code block is found, fall back to another pattern match or handle the absence as needed
        extracted_code = ""

    return extracted_code.strip()


def generate_sql_query(nl_query, filters):
    """
    IMPORTANT: All SQL queries should exclusively use the 'canadapost' table and reference only its columns as detailed in the data dictionary below. 
    Do not include or refer to any columns or tables not listed in this dictionary. 
    """

    # The base WHERE clause is determined by the natural language query
    # This will be dynamically constructed by the language model, so you don't need to hardcode it
    # Just ensure that your prompt instructs the model to consider "Origin Miss Cut-off" as part of the WHERE clause

    # Initialize the WHERE clauses list to accumulate additional filters
    where_clauses = []

    # Check if stream filter is applied and not "All"
    if filters['stream'] != "All" and filters['stream'] != "not defined as variable":
        where_clauses.append(f"STREAM = '{filters['stream']}'")

    # Check if link filter is applied and not "not defined as variable"
    if filters["link"] != "All" and filters["link"] != "not defined as variable":
        where_clauses.append(f"LINKS = '{filters['link']}'")

    # If there are additional filters, we append them to the WHERE clause
    # The user's natural language query will be transformed into the base of the WHERE clause by the LLM
    # Then, we add any additional filters specified via the Streamlit UI
    additional_filters = " AND ".join(where_clauses)
    if additional_filters:
        additional_filters = " AND " + additional_filters


    # Format the data dictionary into a string to include in the prompt
    data_dict_str = "\n".join([f"{key}: {value}" for key, value in data_dictionary.items()])

    instruction_for_strict_table_use = """
    When generating SQL queries, strictly use the 'canadapost' table from the PostgreSQL database. 
    This table includes specific columns as outlined in the provided data dictionary. 
    Directly translate details from the user's question into SQL queries, ensuring that all conditions, filters, and selections strictly adhere to the 'canadapost' table's schema. Do not include or refer to any other table in the queries. 
    The aim should be to extract meaningful insights based on the columns of the 'canadapost' table alone.
    """

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
    When generating SQL queries based on the user's question, it's crucial to match the conditions exactly as specified. For questions concerning specific links, such as "Toronto >> Toronto", you must use the 'LINKS' column directly in the WHERE clause of the SQL query. Directly translate specific details from the question into the SQL query. 
    For instance, if the query mentions a specific link "Toronto >> Toronto", use WHERE LINKS = 'Toronto >> Toronto' in your SQL query, do not use 'DESTINATION_REGION' or 'ORIGIN_REGION'.
    
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
    
    # Dynamic example query based on the instruction
    specific_example_query = """
    Question: The top [N] customers by number of defects
    SQL query:
    SELECT CUSTOMER_NAME, SUM(DP0_VOL) AS FAILURE_COUNT
    FROM CANADAPOST
    WHERE CUSTOMER_NAME IS NOT NULL -- if necessary exclude NULL values from results
    GROUP BY CUSTOMER_NAME
    ORDER BY FAILURE_COUNT DESC
    LIMIT [N]
    """

    # Constructing the prompt with the added instruction, example rows, and the user's task
    prompt = f"""

    Data Dictionary for canadapost:
    {data_dict_str}

    Example query:
    {specific_example_query}

    Three sample rows from canadapost table
    {example_rows}

    Instructions:    
    {instruction_for_strict_table_use}
    {instruction_for_category}
    {instruction_for_failure_category}
    {instruction_for_failure}
    {instruction_for_link}

    Remember:
    - Do not use 'GROUP BY *'. Only include a 'GROUP BY' clause if grouping by specific columns.
    - Ensure the SQL query is ready to execute and adheres to standard SQL syntax.

    Task: Translate the following question into an SQL query and include the appropriate filters.
    User request: "{nl_query}". Do not use spaces or underscores in aliases.
    Please apply all filters within the WHERE clause to directly affect the result set. 
    Do not place any filter conditions as comments—they must be part of the executable SQL command. 
    Here are the filters: "{additional_filters}". Incorporate these filters to refine the query results.
    Filters should modify the result set and not be included as comments.
    """

    response = llm.invoke(prompt)  # Invoke the model with the constructed prompt
    print(response)  # Debugging: print the model's full response for inspection

    sql_query = extract_sql_query(response)  # Extract the SQL query from the response
    if not sql_query:
        print("SQL query not found in the model's response.")
        return None
    
    return sql_query


def generate_chart_python_llm(sql_output):
    # Filter out the None values and replace them with 'Unknown'
    filtered_sql_output = [(name if name is not None else 'Unknown', value) for name, value in sql_output]

    # Convert the filtered SQL output data into a pandas DataFrame
    df = pd.DataFrame(filtered_sql_output, columns=['Name', 'Values'])

    # Create a bar plot using matplotlib
    plt.figure(figsize=(10, 8))  # Adjust the figure size to fit all labels
    bars = plt.bar(df['Name'], df['Values'])

    # Rotate x-axis 'Name' labels vertically and adjust margins to prevent labels from being cut off
    plt.xticks(rotation=90)
    plt.subplots_adjust(bottom=0.2)

    # Add value labels on top of the bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval, int(yval), va='bottom')  # va='bottom' to ensure they're just above the bar

    # Set labels
    plt.xlabel('Name')
    plt.ylabel('Values')

    # Save the visualization as 'output.png'
    plt.savefig('output.png', bbox_inches='tight')

    # Display the plot
    plt.show()
    
    return 'output.png'  # Return the path to the saved image file




def log_to_csv_file(question, sql_query, response):
    with open("chatbot_log.csv", "a", newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([timestamp, question, sql_query, response])

    
    ###### Implementation Calling ###### try to do it optimize higher level of try except 
def process_user_input_localllm(user_input, filters):
    try:
        # Append 'not None' to the user input
        user_input_modified = user_input.strip()
        # Pass the modified input to the SQL generation function
        text2sql = generate_sql_query(user_input_modified, filters)
        if text2sql:
            results = run_query(text2sql)  # Unpack the tuple returned by run_query
            if results:
                if not results:  # Check if the result set is empty
                    response = "No matching records found."
                elif len(results[0]) == 1:
                    if results[0][0] is not None:
                        # Format the single value with commas as thousand separators
                        response = "{:,}".format(results[0][0])
                    else:
                        # Handle the None result here
                        response = "No matching records found."
                else:
                    # If there are multiple fields, format them with a list structure
                    response = '\n'.join(["{}. {} - {}".format(index + 1, row[0] if row[0] is not None else "Unknown", "{:,}".format(row[1]) if row[1] is not None else "Unknown") for index, row in enumerate(results)])


            else:
                response = "Please try again."
        print(response)  # This will print the formatted result in the terminal
        log_to_csv_file(user_input, text2sql, response)  # Log the interaction to CSV
        return response, results
    except Exception as e:
        output_error = f"There has been an error with the code. {e}"
        return output_error, None


# Define Python code Generating and cleaning
def process_sql_output_python_llm(sql_output):
    try:
        llm_python = generate_chart_python_llm(sql_output)
        python_clean = python_parse(llm_python)
        return python_clean
    except Exception as e:
        error = f"An error occurred: {e}"
        return error