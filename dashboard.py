__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
from chat_responses import LMMentorBot

st.title("CS Learning Assistant")


st.title("CS Learning Assistant")

# Initialize session state
if "chatBot" not in st.session_state:
    st.session_state.chatBot = LMMentorBot()

# Initialize messages if not in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to learn about?"):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Get bot response
    response = st.session_state.chatBot.get_response(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

# Reset button
if st.button("Reset Conversation"):
    st.session_state.chatBot.reset()
    st.session_state.messages = []
    st.rerun()