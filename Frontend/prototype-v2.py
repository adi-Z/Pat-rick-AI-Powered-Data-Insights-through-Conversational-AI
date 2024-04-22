import streamlit as st
import json


# Top of your main page with logo and header side by side
col1, col2 = st.columns([1, 3])  # Adjust the ratio as needed

with col1:
    st.image('Picture1.png', width=100)  # Adjust width as needed

with col2:
    #font settings
    st.markdown("<h1 style='text-align: left; color: black;'>PATRICK</h1>", unsafe_allow_html=True)
   # st.header('PATRICK')

#-------------------------------------------------------
#sidebar
st.sidebar.title("Choose Model")
if 'model_selected' not in st.session_state:
    st.session_state.model_selected = 'GPT' # Default to GPT, otherwise input box will not be active on page load

#-------------------------------------------------------

def display_chat_interface():
    #st.header(f"Chat with {st.session_state.model_selected} Model")
    st.markdown(f"<h4 style='text-align: center; margin-bottom: 0;'>Chat with {st.session_state.model_selected} Model</h4>", unsafe_allow_html=True)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_prompt" not in st.session_state:
        st.session_state.last_prompt = None

    prompt = st.chat_input("What is up?")
    if prompt:
        st.session_state.last_prompt = prompt  # Store the last prompt
        process_and_display_chat_input(prompt)
    
    

#-------------------------------------------------------

def process_and_display_chat_input(prompt, regenerate=False):
    # Response generation logic
    if regenerate:
        response = f"Regenerated Echo: {prompt}"
    else:
        response = f"Echo: {prompt}"
        
    # For regeneration, we don't append the prompt again, only the response
    if not regenerate:
        st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": response})

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

#-------------------------------------------------------

# Function to save rating (you could replace this with your own logic to save the rating, e.g., to a database)
def save_rating(rating):
    # Placeholder function to simulate saving a rating
    # In a real app, this would save to a database or file
    print(f"Rating received: {rating}")
    # If you have a json file to keep track of the ratings, you could use:
    # with open('ratings.json', 'w') as f:
    #     json.dump(rating, f)

#-------------------------------------------------------

if st.sidebar.button("GPT"):
    st.session_state.model_selected = 'GPT'
if st.sidebar.button("Local"):
    st.session_state.model_selected = 'Local'

if st.session_state.model_selected:
    display_chat_interface()


# Divider
st.markdown("---")  # This creates a horizontal line as a divider

#-------------------------------------------------------

# Control buttons

col1, col2 = st.columns(2)
with col1:
    if st.button('Reset'):
        st.session_state.messages = []
        st.session_state.model_selected = 'GPT'
        st.session_state.last_prompt = None
        # Automatically refresh to clear the chat
        st.experimental_rerun()
with col2:
    if st.button('Regenerate'):
        # Only regenerate if there's a last prompt to use
        if st.session_state.last_prompt:
            process_and_display_chat_input(st.session_state.last_prompt, regenerate=True)
# 





