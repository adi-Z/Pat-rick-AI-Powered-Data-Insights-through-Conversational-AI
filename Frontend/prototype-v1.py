import streamlit as st
import numpy as np

#Ollama Bot function
def local_model():
    st.title("Local Model Bot")

    #Initialize chat hsitory
    if "messages" not in st.session_state:
        st.session_state.messages = []


    #Display chat history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


    #React to user's input
    if prompt := st.chat_input("What is up?"):
            #Display user message in chat message container
            st.chat_message("user").markdown(prompt)
            #Add user's message to the chat history
            st.session_state.messages.append({"role": "user", "content": prompt}) 

            #if prompt contain the word graph, display a graph
            if "graph" in prompt:

                with st.chat_message("assistant"):
                    response = st.line_chart({"data": [1, 5, 2, 6, 2, 1]})
                st.session_state.messages.append({"role": "assistant", "content": response})

            else:
                #Assistant(bot) response
                response = f"Echo: {prompt}"
                #Display assistent response in chat message container
                with st.chat_message("assistant"):
                    st.markdown(response)
                #Add bot's message to the chat history
                st.session_state.messages.append({"role": "assistant", "content": response})


#GPT Bot function
def chat_gpt():
    st.title("GPT Bot")

    #Initialize chat hsitory
    if "messages" not in st.session_state:
        st.session_state.messages = []


    #Display chat history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


    #React to user's input
    if prompt := st.chat_input("What is up?"):
            #Display user message in chat message container
            st.chat_message("user").markdown(prompt)
            #Add user's message to the chat history
            st.session_state.messages.append({"role": "user", "content": prompt}) 

            #if prompt contain the word graph, display a graph
            if "graph" in prompt:

                with st.chat_message("assistant"):
                    response = st.line_chart({"data": [1, 5, 2, 6, 2, 1]})
                st.session_state.messages.append({"role": "assistant", "content": response})

            else:
                #Assistant(bot) response
                response = f"Echo: {prompt}"
                #Display assistent response in chat message container
                with st.chat_message("assistant"):
                    st.markdown(response)
                #Add bot's message to the chat history
                st.session_state.messages.append({"role": "assistant", "content": response})


#Main function
# Sidebar for model selection
model_option = st.sidebar.selectbox("Choose a Model:", ["Chat GPT", "Local Model"])

#Display the selected model's interaction page
if model_option == "Chat GPT":
    chat_gpt()
elif model_option == "Local Model":
    local_model()


