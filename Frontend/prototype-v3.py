import streamlit as st
import csv


# Function to simulate processing the input and generating a response
def process_message(model, from_city, to_city, message):
    # Placeholder function to simulate response generation.
    response = (
        f"The {model} model says: From {from_city} to {to_city}, you said '{message}'."
    )
    return response


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


# Reset chat history
def reset_chat():
    st.session_state.messages = []
    st.rerun()


# Regenerate response
def regenerate_response():
    if st.session_state.messages:
        last_user_message = next(
            (
                message["message"]
                for message in reversed(st.session_state.messages)
                if message["role"] == "user"
            ),
            None,
        )
        if last_user_message:
            new_response = process_message(
                st.session_state.model_selected,
                st.session_state.from_input,
                st.session_state.to_input,
                last_user_message[::-1],
            )
            st.session_state.messages.append(
                {"role": "assistant", "message": new_response}
            )
            st.rerun()


# Set model
def set_model(model_name):
    st.session_state.model_selected = model_name


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "model_selected" not in st.session_state:
    st.session_state.model_selected = "GPT"


# Sidebar for route selection
with st.sidebar:
    st.title("Choose Model")
    # Model selection buttons
    if st.button("GPT Model"):
        set_model("GPT")
    if st.button("Local Model"):
        set_model("Local")

    # Divider
    st.markdown("---")

    st.title("Filter")
    from_input = st.selectbox(
        "Link Origin", link_unique_values_list, index=0, key="from_input"
    )
    to_input = st.selectbox(
        "Link Destination", link_unique_values_list, index=0, key="to_input"
    )


# Display chat history
def display_chat():
    # Main header with logo
    col1, col2 = st.columns([1, 4])  # Adjust the ratio as needed

    with col1:
        st.image(
            "picture1.png", width=100
        )  # Replace 'path_to_logo.png' with the path to your logo

    with col2:
        st.markdown(
            f"""<h1 style='text-align: left; color: black;'>PATRICK - <span>{st.session_state.model_selected} Model</span></h1>""",
            unsafe_allow_html=True,
        )

    user_message = st.chat_input("Send a message", key="chat_input")

    if user_message:
        st.session_state.messages.append(
            {"role": "user", "message": f"You: {user_message}"}
        )
        response = process_message(
            st.session_state.model_selected,
            st.session_state.from_input,
            st.session_state.to_input,
            user_message,
        )
        st.session_state.messages.append(
            {"role": "assistant", "message": f"Patrick: {response}"}
        )

    for chat in st.session_state.messages:
        with st.chat_message(chat["role"]):
            st.markdown(chat["message"])


# Control buttons for reset and regenerate
def control_buttons():
    col1, col2, col3 = st.columns(
        (0.25, 0.35, 0.35)
    )  # Create 3 columns with the specified width ratio
    with col1:  # Align items to the left within the second column
        if st.button("📈 Generate Chart"):
            regenerate_response()
    with col2:  # Align items to the left within the second column
        if st.button("♻️ Regenerate Last Response"):
            regenerate_response()
    with col3:  # Align items to the left within the first column
        if st.button("🔄 Reset Chat"):
            reset_chat()
    st.write("")  # Add empty space between columns


# Main
display_chat()
control_buttons()
