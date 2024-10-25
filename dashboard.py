__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
from chat_responses import LMMentorBot

# Set page configuration
st.set_page_config(
    page_title="Conmodus - Your Tech Learning Assistant",
    page_icon="🤖",
    layout="wide"
)
uploaded_file = st.sidebar.file_uploader(
    "Upload a file for context (PDF or TXT)",
    type=["pdf", "txt"],
    help="Upload a file to provide context for our conversation. Conmodus will use this information to provide more relevant responses."
)

# Process uploaded file
if uploaded_file and "file_processed" not in st.session_state:
    with st.spinner("Processing file..."):
        response = st.session_state.chatBot.upload_file(uploaded_file)
        st.sidebar.success(response)
        st.session_state.file_processed = True

# Add file status indicator
if "file_processed" in st.session_state:
    st.sidebar.info(f"Currently using: {uploaded_file.name}")
    if st.sidebar.button("Remove File Context"):
        st.session_state.chatBot.reset()
        del st.session_state.file_processed
        st.rerun()
# Add custom CSS
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
    .quiz-mode {
        background-color: #2c3e50;
        color: #ecf0f1;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .quiz-mode a {
        color: #3498db;
        text-decoration: underline;
    }
    .quiz-mode strong, .quiz-mode b {
        color: #f39c12;
    }
    .quiz-mode em, .quiz-mode i {
        color: #2ecc71;
    }
    .socratic-mode {
        background-color: #d4edda;
        color: #333333;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
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

# Initialize session state
if "chatBot" not in st.session_state:
    st.session_state.chatBot = LMMentorBot()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Header with improved styling
st.title("👩‍💻 Conmodus - Technical Assistant for Responsible AI")
st.markdown("""
    <div class="header-description">
    Welcome! I'm Conmodus, your AI learning companion. Through our dialogue, I'll help you:
    
    • Understand programming concepts through guided discovery
    • Learn about AI and its responsible use in technology
    • Develop technical skills at your own pace
    • Think critically about software development
    
    Ask me anything about programming, AI, or technology!
    </div>
    """, unsafe_allow_html=True)

# Main chat interface
chat_container = st.container()

# Display chat messages
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(f"<div class='{message['role']}-message'>{message['content']}</div>", 
                       unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("What would you like to learn about?"):
    # Display user message
    with st.chat_message("user"):
        st.markdown(f"<div class='user-message'>{prompt}</div>", 
                   unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Get bot response
    response = st.session_state.chatBot.process_query(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(f"<div class='assistant-message'>{response}</div>", 
                   unsafe_allow_html=True)
    st.session_state.messages.append({"role": "assistant", "content": response})

# Reset conversation button (simplified)
if st.button("Start New Conversation"):
    st.session_state.chatBot.reset()
    st.session_state.messages = []
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666;'>
    Powered by Conmodous | Making technical education more accessible and supportive
    </div>
    """, unsafe_allow_html=True)
