__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import re
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

# Custom CSS
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
    .quiz-button {
        margin: 0.25rem 0;
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

def parse_options(text):
    """Parse [OPTIONS]...[/OPTIONS] block from response"""
    pattern = r'\[OPTIONS\](.*?)\[/OPTIONS\]'
    match = re.search(pattern, text, re.DOTALL)

    if match:
        options_text = match.group(1).strip()
        # Parse individual options (A), B), etc.)
        options = re.findall(r'([A-D])\)\s*(.+?)(?=(?:[A-D]\)|$))', options_text, re.DOTALL)
        options = [(letter, text.strip()) for letter, text in options]

        # Get the message without the options block
        message_without_options = text[:match.start()] + text[match.end():]
        message_without_options = message_without_options.strip()

        return message_without_options, options

    return text, []

def display_message_with_options(content, message_idx):
    """Display a message and its quiz options as buttons"""
    message_text, options = parse_options(content)

    # Display the message text
    st.markdown(message_text)

    # Display options as buttons if present
    if options:
        st.markdown("**Select your answer:**")
        cols = st.columns(len(options))
        for i, (letter, option_text) in enumerate(options):
            with cols[i]:
                button_label = f"{letter}) {option_text[:50]}..." if len(option_text) > 50 else f"{letter}) {option_text}"
                if st.button(button_label, key=f"opt_{message_idx}_{letter}", use_container_width=True):
                    st.session_state.pending_input = f"{letter}) {option_text}"
                    st.rerun()

# Initialize chat bot
if "chatBot" not in st.session_state:
    st.session_state.chatBot = LMMentorBot()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize pending input (for quiz button clicks)
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None

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
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                # Check if this is the last assistant message (show interactive buttons)
                is_last_assistant = idx == len(st.session_state.messages) - 1
                if is_last_assistant:
                    display_message_with_options(message["content"], idx)
                else:
                    # For older messages, just show text without options block
                    text_only, _ = parse_options(message["content"])
                    st.markdown(text_only)
            else:
                st.markdown(message["content"])

# Handle pending input from quiz button click
if st.session_state.pending_input:
    pending = st.session_state.pending_input
    st.session_state.pending_input = None

    # Display user message
    with st.chat_message("user"):
        st.markdown(pending)

    # Get and display assistant response
    with st.chat_message("assistant"):
        response = st.session_state.chatBot.chat_stream(pending)

    # Store messages
    st.session_state.messages.append({"role": "user", "content": pending})
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

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
    st.rerun()


st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666;'>
    Powered by Conmodus | Making technical education more accessible and supportive
    </div>
    """, unsafe_allow_html=True)
