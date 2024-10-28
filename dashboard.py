__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
from chat_responses import LMMentorBot
from audit_parse import extract_text_fromaudit
from feedback import append_values

# Set page configuration
st.set_page_config(
    page_title="Conmodus - Your Tech Learning Assistant",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS (unchanged)
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .css-1d391kg {
        padding: 2rem 1rem;
    }
    .user-message {
        background-color: #f0f2f6;
        color: #333333;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .assistant-message {
        background-color: #e8f0fe;
        color: #333333;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-size: 1.1em;
        line-height: 1.6;
    }
    .message-container {
        margin-bottom: 1.5rem;
    }
    .header-description {
        color: #666;
        font-size: 1.1em;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Header
st.title("👩‍💻 Conmodus - Technical Assistant for Responsible AI")
st.markdown("""
    <div class="header-description">
    Welcome! I'm Conmodus, your AI learning companion. Through our dialogue, I'll help you:
    
    • Understand course concepts through guided discovery
    • Master the material and find answers through conversation
    • Develop technical skills at your own pace
    • Think critically about software development
    </div>
    """, unsafe_allow_html=True)

# Initialize chat bot
if "chatBot" not in st.session_state:
    st.session_state.chatBot = LMMentorBot()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for file upload
with st.sidebar:
    uploaded_file = st.file_uploader(
        "Upload a file for context (PDF or TXT)",
        type=["pdf", "txt"],
        help="Upload a file to provide context for our conversation. Conmodus will use this information to provide more relevant responses."
    )

    if uploaded_file and "file_processed" not in st.session_state:
        with st.spinner("Processing file..."):
            response = st.session_state.chatBot.upload_file(uploaded_file)
            st.sidebar.success(response)
            st.session_state.file_processed = True

    if "file_processed" in st.session_state:
        st.sidebar.info(f"Currently using: {uploaded_file.name}")
        if st.sidebar.button("Remove File Context"):
            st.session_state.chatBot.reset()
            del st.session_state.file_processed
            st.rerun()

# Main chat interface
chat_container = st.container()

# Display chat messages
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(f"<div class='{message['role']}-message'>{message['content']}</div>", 
                       unsafe_allow_html=True)

# # Chat input
# if prompt := st.chat_input("What would you like to learn about?"):
#     # Display user message
#     with st.chat_message("user"):
#         st.markdown(f"<div class='user-message'>{prompt}</div>", 
#                    unsafe_allow_html=True)
#     st.session_state.messages.append({"role": "user", "content": prompt})

#     # Get bot response
#     with st.chat_message("assistant"):
#         message_placeholder = st.empty()
#         full_response = ""
        
#         # Stream the response
#         for chunk in st.session_state.chatBot.chat_stream(prompt):
#             full_response += chunk
#             message_placeholder.markdown(f"<div class='assistant-message'>{full_response}</div>", 
#                                       unsafe_allow_html=True)
    
#     # Store the full response
#     st.session_state.messages.append({"role": "assistant", "content": full_response})

# Chat input
if prompt := st.chat_input("What would you like to learn about?"):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get and display assistant response
    with st.chat_message("assistant"):
        response = st.session_state.chatBot.chat_stream(prompt)
        
    # Store messages
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": response})


st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666;'>
    Powered by Conmodus | Making technical education more accessible and supportive
    </div>
    """, unsafe_allow_html=True)