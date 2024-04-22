import streamlit as st
import csv
import sys
from PIL import Image
import random
import matplotlib.pyplot as plt
import pandas as pd

# Add the directory containing the notebook file to the system path
sys.path.append(".")
from gptllm import process_user_input, process_sql_output_python
from localllm import process_user_input_localllm

# Function to read unique values from a CSV file
def read_unique_values(file_path):
    unique_values = set()
    with open(file_path, newline="", encoding="latin-1") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            for value in row:
                unique_values.add(value.strip())  # Remove leading and trailing spaces
    return unique_values


# Read and process the text file
unique_values = read_unique_values("links.csv")
link_unique_values_list = list(unique_values)
link_unique_values_list.insert(0, "All")
link_unique_values_list.sort()


# Generate chart
def generate_chart():
    error_count = 0
    while error_count < 2:  # Allow two attempts
        try:
            if st.session_state.model_selected == "GPT":
                # Generate the Python code from SQL output and execute it
                st.session_state.python_code = process_sql_output_python(st.session_state.sql_output)
                exec(st.session_state.python_code)  # Execute the Python plotting code
                image_path = 'output.png'  # The path where the plot is saved
                image = Image.open(image_path)
                with st.container():
                    st.image(image, use_column_width='auto')
                break  # Break out of the loop if successful
            elif st.session_state.model_selected == "Local":
                if len(st.session_state.sql_output) > 1:
                    filtered_sql_output = [
                        (name if name is not None else 'Unknown', value)
                        for name, value in st.session_state.sql_output
                    ]
                    df = pd.DataFrame(filtered_sql_output, columns=['Name', 'Values'])
                    # Sort the DataFrame in descending order by 'Values'
                    df = df.sort_values('Values', ascending=False)
                    total = df['Values'].sum()  # Calculate the total sum of values
                    
                    plt.figure(figsize=(10, 8))
                    bars = plt.bar(df['Name'], df['Values'])
                    plt.xticks(rotation=90)
                    plt.xlabel('Name')
                    plt.ylabel('Values')
                    plt.tight_layout()
                    
                    for bar in bars:
                        yval = bar.get_height()
                        percentage = (yval / total) * 100  # Calculate the percentage
                        label = f"{int(yval)}\n({percentage:.1f}%)"
                        plt.text(bar.get_x() + bar.get_width() / 2, yval, label, va='bottom', ha='center')
                    

                    # Save the plot to a file
                    plt.savefig('output.png', bbox_inches='tight')
                    plt.close()  # Close the figure to prevent it from displaying in the notebook/output

                    # Load and display the image in Streamlit
                    image_path = 'output.png'  # Update this path if needed
                    image = Image.open(image_path)
                    with st.container():
                        st.image(image, use_column_width='auto')
                else:
                    st.info("Not enough data to generate a chart.")
                break  # If successful, exit loop
            else:
                st.error("Model not selected.")
                break

        except Exception as e:
            error_count += 1
            st.error(f"Attempt {error_count}: Failed to generate or display the chart. Error: {e}")
            if error_count >= 2:
                st.error("Max attempts reached. Please try again or contact support.")
                break  # Exit the loop after maximum attempts reached



# Reset chat history
def reset_chat():
    st.session_state.messages = []
    st.rerun()


# Regenerate response
def regenerate_response():
    if st.session_state.messages:
        last_user_message = None
        for message in reversed(st.session_state.messages):
            if message["role"] == "user" and "message" in message:
                last_user_message = message["message"][len("You: "):]  # Removing the "You: " prefix
                break

        if last_user_message is not None:
            # Process the message using the selected model
            if st.session_state.model_selected == "GPT":
                response, st.session_state.sql_output, sql_query = process_user_input(
                    last_user_message, filters
                )
            elif st.session_state.model_selected == "Local":
                response, st.session_state.sql_output = process_user_input_localllm(
                    last_user_message, filters
                )
            else:
                response = "Model not selected. Please choose a model to generate the response."

            # Append the response to the messages list
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "message": f"Patrick: \n{response}"
                }
            )
            st.rerun()
        else:
            # Handle case where last user message or 'message' key is not found
            st.error("Could not find the last user message to regenerate the response.")


# Set model
def set_model(model_name):
    st.session_state.model_selected = model_name


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "model_selected" not in st.session_state:
    st.session_state.model_selected = "Local"


# Sidebar for route selection
with st.sidebar:
    st.title("Choose Model")

    # Create two columns for displaying buttons next to each other
    col1, col2 = st.columns(2)
    # Model selection buttons
    if col1.button("GPT Model"):
        set_model("GPT")

    if col2.button("Local Model"):
        set_model("Local")
    # Divider
    st.markdown("---")

    st.title("Link Filter")
    from_input = st.selectbox(
        "Link Origin", link_unique_values_list, index=0, key="from_input"
    )
    to_input = st.selectbox(
        "Link Destination", link_unique_values_list, index=0, key="to_input"
    )
    # Add a validator message
    if from_input == "All" and to_input != "All":
        st.error(
            "Please select 'All' in both origin and destination or a valid combination of locations."
        )
    elif from_input != "All" and to_input == "All":
        st.error(
            "Please select 'All' in both origin and destination or a valid combination of locations."
        )

    st.title("Stream Filter")
    stream_input = st.selectbox(
        "Stream",
        ["All", "Stream 1", "Stream 2", "Stream 3"],
        index=0,
        key="stream_input",
    )

    filters = {}
    # Set filters if all is selected then set "not defined as variable"
    if from_input == "All" or to_input == "All":
        filters["link"] = "not defined as variable"
    else:
        filters["link"] = from_input + " >> " + to_input
    if stream_input == "All":
        filters["stream"] = "not defined as variable"
    else:
        filters["stream"] = stream_input

    st.session_state.filters = filters


# Display chat history
def enterprise_llm():
    # Main header with logo
    col1, col2 = st.columns([1, 4])  # Adjust the ratio as needed

    with col1:
        st.image(
            "Picture1.png", width=100
        )  # Replace 'path_to_logo.png' with the path to your logo

    with col2:
        st.markdown(
            f"""<h1 style='text-align: left; color: black;'>PATRICK - <span>{st.session_state.model_selected} Model</span></h1>""",
            unsafe_allow_html=True,
        )

    user_message = st.chat_input("Send a message", key="chat_input")

    if user_message:
        st.toast("Let me do some searching🔍...")
        st.session_state.messages.append(
            {"role": "user", "message": f"You: {user_message}"}
        )
        filters = st.session_state.filters
        # random_message = random.choice(messages)
        # st.toast(random_message)
        response, st.session_state.sql_output, sql_query = process_user_input(
            user_message, filters
        )
        st.toast("I found something🎉!")
        output = {
            "role": "assistant",
            "message": f"""
                Patrick: {response}
                
                """,
        }
        st.session_state.messages.append(output)

    for chat in st.session_state.messages:
        with st.chat_message(chat["role"]):
            st.markdown(chat["message"])

# Ollama Bot function
def local_model():
    # Main header with logo
    col1, col2 = st.columns([1, 4])  # Adjust the ratio as needed

    with col1:
        st.image(
            "Picture1.png", width=100
        )  # Replace 'path_to_logo.png' with the path to your logo

    with col2:
        st.markdown(
            f"""<h1 style='text-align: left; color: black;'>PATRICK - <span>{st.session_state.model_selected} Model</span></h1>""",
            unsafe_allow_html=True,
        )

    #st.title("On premise Model Bot: Ollama")

    # Initialize chat hsitory
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["message"])

    # React to user's input
    if prompt := st.chat_input("How can I help you?"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user's message to the chat history
        st.session_state.messages.append({"role": "user", "message": f"You: {prompt}"})

        # Assistant(bot) response
        filters = st.session_state.filters
        st.session_state.response, st.session_state.sql_output  = process_user_input_localllm(prompt, filters)
        
        # Display assistent response in chat message container
        with st.chat_message("assistant"):
            st.markdown(st.session_state.response, unsafe_allow_html=True)
        # Add bot's message to the chat history
        st.session_state.messages.append({"role": "assistant", "message": f"Patrick: \n{st.session_state.response}"})

# Control buttons for reset and regenerate
def control_buttons():
    col1, col2, col3 = st.columns(
        (0.25, 0.35, 0.35)
    )  # Create 3 columns with the specified width ratio
    with col1:  # Align items to the left within the second column
        if st.button("📈 Generate Chart"):
            generate_chart()
    with col2:  # Align items to the left within the second column
        if st.button("♻️ Regenerate Last Response"):
            regenerate_response()
    with col3:  # Align items to the left within the first column
        if st.button("🔄 Reset Chat"):
            reset_chat()
    st.write("")  # Add empty space between columns


messages = [
    "Hold on, ninja squirrels incoming!",
    "Tech gremlins at your service!",
    "Data wizards on it!",
    "IT hamsters on duty!",
    "Summoning digital gnomes!",
    "Binary spells in progress!",
    "Cyber pigeons en route!",
    "Wi-Fi signal getting stronger!",
    "Coffee-fueled server elves engaged!",
    "Internet scrolls being unrolled!",
]

# Main
# Display the selected model's interaction page
if st.session_state.model_selected == "GPT":
    enterprise_llm()

elif st.session_state.model_selected == "Local":
    local_model()

control_buttons()
