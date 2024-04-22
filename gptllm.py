# #Imports
from langchain_community.utilities import SQLDatabase
import re
import csv
import datetime
import asyncio

# from langchain_community.chat_models import ChatOllama #For ollama implementation
from langchain_openai import ChatOpenAI

# Create an instance of SQLDatabase using the database connection parameters
db = SQLDatabase.from_uri(
    "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",#Use your MYSQL URI
    sample_rows_in_table_info=3,
)
## Implementation ##

# LLM Instance
# (Temperature is a value that ranges from 0 to 1, determining the degree of randomness/creativity (0) to precision/predictability (1) in the output.)

# OpenAI - Enterprise ChatGPT
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    api_key="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",#Use your API key
)

# Database Instance
db = SQLDatabase.from_uri(
    "mysql://algonquin:Canada2023*@deved.sytes.net:3306/canada_post",
    sample_rows_in_table_info=3,
)


# Get the table schema
def get_table_schema(table_name):
    table_schema = db.get_table_info(table_name)
    return table_schema


# Run Sql query
def run_sql_query(sql_query):
    result = db.run(sql_query, include_columns=True)
    return result


### Context
# Data dictionary for the CANADAPOST table
data_dictionary = {
    "FYFW": "Fiscal Year Fiscal Week",
    "Origin_Date": "The day when the item was first received by Canada post within that FYFW.",
    "FAIL": "T if the Items failed and F if it did not fail to meet the required criteria.",
    "CUSTOMER_NAME": "Name of the commercial Customer, exclude null or '' names when used to list more than 1 Customer(e.g. <> ''), When calculating totals, include all customers.",
    "ORIGIN_REGION": "Five regions where the post is originated from: Pacific, GTA, Atlantic, Ontario, Quebec, Prairie.",
    "LINK": "The link on which the parcel originated from and the destination to be delivered, example 'Toronto >> North bay', it's conformed by Canadian cities.",
    "DESTINATION_REGION": "Five regions where the post is destined to: Pacific, GTA, Atlantic, Ontario, Quebec, Prairie.",
    "WORK_CENTER_NAME": "The name of the work center or also called sorters where the items got scanned,  exclude null or '' names when used to list more than 1 Customer(e.g. <> ''), When calculating totals, include all work centers.",
    "FAILURE_CATEGORY": "Category in which the item failed during the entire process. Possible values include: CPC Missort (WC Known), CPC Missort (WC Unknown), Depot Miss Cut-off (DSS After 11), Depot on-time (DSS Before 11) delivered late / End..., Late Origin Plant Processing (After 12 PM Retail), Ontime, Origin Miss Cut-off, Other, Processed after destination plant cut-off prior to..., Processed at destination plant after 12pm, Unknown.",
    "STREAM": "3 streams: Stream 1, Stream 2, Stream 3.",
    "DP0_VOL": "Volume of failed/errors/defects items on any type of aggregation. To find total failures or how many failures/errors/defects happened, always use the SUM function; DO NOT USE COUNT(*) FUNCTION; do not ignore other filters.",
}
# Format the data dictionary into a string to include in the prompt as context
data_dict_str = "\n".join([f"{key}: {value}" for key, value in data_dictionary.items()])

# Example, conformed by a Question an a Sql query
specific_example_query = f"""
    CONTEXT1:
    Question: What are top 10 customers by number of defects?
    SQL query:
    SELECT CUSTOMER_NAME, SUM(DP0_VOL) AS FAILURE_COUNT FROM shipment_data WHERE CUSTOMER_NAME <> '' AND FAIL='T' GROUP BY CUSTOMER_NAME ORDER BY FAILURE_COUNT DESC limit 10;
    
    CONTEXT2:
    Question: What is the total number of failures and what percentage is it for the link Montreal >> Kelowna?
    SQL query:
    [SELECT 
    SUM(CASE WHEN FAIL = 'T' THEN DP0_VOL ELSE 0 END) AS Total_Failures,
    (SUM(CASE WHEN FAIL = 'T' THEN DP0_VOL ELSE 0 END) / SUM(DP0_VOL)) * 100 AS Failure_Percentage
FROM 
    shipment_data
WHERE 
    LINK = 'Montreal >> Kelowna';]
    """


# Look for SQL query within the model's response
def extract_sql_query(model_response):
    pattern = r"SELECT\s+.*?;"
    sql_query = re.search(
        pattern, str(model_response.content), re.IGNORECASE | re.DOTALL
    )
    if sql_query:
        sql_query_str = sql_query.group().strip()  # Remove leading/trailing whitespace
        sql_query_stripped = sql_query_str.replace(
            "\n", " "
        ).strip()  # Replace newline characters with spaces
        return sql_query_stripped
    else:
        error = "SQL query not found in the model's response."
        return error


# Python Code cleaner
def python_parse(llm_code):
    llm_code_str = str(llm_code.content)
    # Regular expression pattern to match Python code within triple backticks or without backticks
    pattern = r"```?python(.*?)```?|\bimport\b.*?plt\.show\(\)"
    # Find all matches of the pattern in the template
    matches = re.findall(pattern, llm_code_str, re.DOTALL)
    # Join the matches to get the extracted Python code
    extracted_code = "\n".join(matches)
    return extracted_code.strip()


# LLM Text 2 SQL conversion
def generate_sql_query(question, filters):
    # Define variables
    Dialect = db.dialect
    Table_Schema = db.get_table_info()
    Data_Dict_Str = data_dict_str

    # Prompt template
    prompt = f"""
              Refined Prompt:
                Given the provided question, data dictionary, example queries, and user filters:

                -Your task is to transform the question into a MySQL query using the 'shipment_data' table. Be analytical and precise, adhering closely to the requirements outlined below.
                -Your output should consist solely of the SQL query, without any additional commentary or preamble.
                -Ensure that your query handles scenarios such as empty customer names appropriately. For instance, if the task is to retrieve the top 10 customers, exclude entries with empty ('') customer names from consideration but still provide a list of 10 customers in your response., but when doing a total count, include all customers.
                -DO NOT USE COUNT(*) FUNCTION; do not ignore other filters.

              Question:
              {question}

              User filters:
              Stream =  {filters['stream']}
              Link = {filters['link']}

              Here is a sample question with a query output(Is just an example is not part of the question, is just to give you context):
              [{specific_example_query}]

              Here is the data dictionary, is very important to use this:
              [{data_dict_str}]
              
              Before continuing with your sql query generation, take a moment to reflect on your own experiences, beliefs, and biases related to the topic. Consider how these factors might influence your perspective and the arguments you present. Once you've taken some time for reflection, proceed with the task at hand.
              """
    response = llm.invoke(prompt)  # Adjust as per your model's API call structure
    sql_query = extract_sql_query(response)  # Extract the SQL query from the response
    return sql_query


# SQL to Natural Language Query Response
def generate_nl_response(question, sql_query_output):
    if not sql_query_output:
        return "I'm sorry, I'm not able to find the answer to your question."
    # Prompt template
    prompt = f"""
    Based on the following User question and SQL Output, write a natural language response.

    ** Important!! IF the final output is a SQL CODE, you must answer "I'm sorry, I'm not able to find the answer to your question". **

    Use all the information provided to generate a full coherent response. No pre-amble.

    User question:
    "{question}"

    SQL_query:
    {sql_query_output}
    """
    nl_response = llm.invoke(prompt)  # Adjust as per your model's API call structure
    return nl_response.content


# SQL to python output
def generate_chart_python(sql_output):
    prompt = f"""
    using output_data = [{sql_output}]
    Follow the instructions below to process MySQL output data and generate a visually appealing visualization using Python:

    1. **Prepare the Data**:
    - Use the provided output_data and convert it into a pandas DataFrame.
    - Ensure readability by handling any necessary transformations and removing MySQL data types like Decimal, String, Object, Etc.
    - Avoid the  NameError: name 'Decimal' is not defined


    2. **Visualize the Data**:
    - Write a Python script to visualize the data using Seaborn.
    - Choose an appropriate plot type based on the data distribution and insights to be conveyed.
    - Count the number of rows so IF it is 1, create a 'KPI card' with the column title and a prominent value, styled like a Power BI visualization, otherwise create a plot.
    - Ensure the visualization is aesthetically pleasing and effectively communicates insights.
    - Enhance readability by including value labels based on the number of rows.

    3. **Additional Script Requirements**:
    - Suppress Python warnings to maintain clean output.
    - If the MySQL output consists of a single object, create a 'KPI card' with the column title and a prominent value, styled like a Power BI visualization.

    4. **Script Consolidation**:
    - Consolidate all instructions into a single Python script for ease of execution.
    - Remove unnecessary redundancy, ensuring the script remains concise and efficient.

    5. **Save Output**:
    - Save the final visualization as 'output.png' with a tight bounding box to capture the entire chart.

    Ensure adherence to these instructions for optimal execution of the Python script. 

    python:[] 
    """
    llm_code = llm.invoke(prompt)
    # python_middleware = python_parse(llm_code)
    # python_output = python_run()
    return llm_code


# Log the interaction to a CSV file for debugging and analysis
def log_to_csv_file(
    user_input, generated_sql_query, sql_query_results, natural_language_response
):
    try:
        with open("chatbot_log.csv", "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter="|")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow(
                [
                    timestamp,
                    user_input,
                    generated_sql_query,
                    sql_query_results.replace("\n", " "),
                    natural_language_response.replace("\n", " "),
                ]
            )
    except Exception as e:
        print(f"Error occurred while logging to CSV: {e}")


####################


# Define function to process user input
def process_user_input(user_input, filters):
    try:
        sql_query = generate_sql_query(
            user_input, filters
        )  # Generate SQL query based on user input
        sql_output = run_sql_query(
            sql_query
        )  # Run Sql Query and store it on a variable
        nl_response = generate_nl_response(
            user_input, sql_output
        )  # Parse the sql output into a NL
        # log_to_csv_file(user_input, sql_query, sql_output, nl_response)
        return nl_response, sql_output, sql_query
    except Exception as e:
        log_to_csv_file(
            user_input,
            "Error occurred",
            f"An error occurred: {e}",
            "Sorry, I'm unable to answer your question due to an unexpected error. Let's try again.",
        )
        error = f"An error occurred: {e}"
        return error, error, error


# Define Python code Generating and cleaning
def process_sql_output_python(sql_output):
    try:
        llm_python = generate_chart_python(sql_output)
        python_clean = python_parse(llm_python)
        return python_clean
    except Exception as e:
        error = f"An error occurred: {e}"
        return error



