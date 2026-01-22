import os
import streamlit as st
from typing import Optional, Dict
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()  # Load from .env file
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.vectorstores import Chroma
from file_parser import FileParser

class LMMentorBot:
    def __init__(self):
        try:
            # Initialize API keys - try st.secrets first, then env vars
            self.google_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY", "")

            if not self.google_key:
                raise KeyError("GEMINI_API_KEY not found")

            self.setup_environment()

            # Initialize core components - using Gemini for both chat and embeddings
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=self.google_key,
                temperature=0.7,
                streaming=True,
            )

            self.file_parser = FileParser(self.google_key)
            
        except KeyError:
            st.error("Required API keys not found in secrets. Please add them to your Streamlit secrets.")
            st.stop()

        # Initialize storage and state
        self.store: Dict[str, ChatMessageHistory] = {}
        self.vector_store: Optional[Chroma] = None
        self.default_chain = None
        self.rag_chain = None

        
        # Setup default conversation chain
        self.setup_default_chain()

    def setup_environment(self):
        """Setup environment variables"""
        langchain_key = st.secrets.get("LANGCHAIN_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
        if langchain_key:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
            os.environ["LANGCHAIN_API_KEY"] = langchain_key

    def setup_default_chain(self):
        """Set up the default conversation chain without RAG"""
        with open("prompts/mentor_prompt.txt", "r") as f:
            mentor_prompt = f.read()

        default_template = ChatPromptTemplate.from_messages([
            ("system", mentor_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

        self.default_chain = RunnableWithMessageHistory(
            (lambda x: {"input": x["input"], "context": "", "chat_history": x["chat_history"]}) |
            default_template |
            self.llm,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="output"
        )

    def setup_rag_chain(self):
        """Set up the RAG chain with prompts and retrievers"""
        if not self.vector_store:
            return

        # Load prompts
        with open("prompts/retriever_prompt.txt", "r") as f:
            retriever_prompt = f.read()
        
        with open("prompts/mentor_prompt.txt", "r") as f:
            mentor_prompt = f.read()

        # Create prompt templates
        retriever_template = ChatPromptTemplate.from_messages([
            ("system", retriever_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

        mentor_template = ChatPromptTemplate.from_messages([
            ("system", mentor_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            ("system", "Context: {context}")
        ])

        # Set up history-aware retriever
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}
        )
        
        history_aware_retriever = create_history_aware_retriever(
            self.llm,
            retriever,
            retriever_template
        )
        
        # Create document chain
        document_chain = create_stuff_documents_chain(
            llm=self.llm,
            prompt=mentor_template,
            document_variable_name="context"
        )
        
        # Create retrieval chain with proper chat history handling
        retrieval_chain = (
            {
                "context": history_aware_retriever, 
                "input": lambda x: x["input"],
                "chat_history": lambda x: x.get("chat_history", [])
            } 
            | document_chain
        )
        
        # Wrap in RunnableWithMessageHistory
        self.rag_chain = RunnableWithMessageHistory(
            retrieval_chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="output"
        )
    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """Get or create chat history for a session"""
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]

    def upload_file(self, uploaded_file) -> str:
        """Process uploaded file and create vector store for context"""
        try:
            self.vector_store = self.file_parser.parse_file(uploaded_file)
            if self.vector_store:
                self.setup_rag_chain()
                return f"Successfully processed {uploaded_file.name}. Ready for context-aware responses!"
            return "No file uploaded."
        except Exception as e:
            return str(e)

    def chat(self, text: str, session_id: str = "default") -> str:
        """Process a chat message and return response"""
        try:
            # Use RAG chain if available, otherwise use default chain
            chain = self.rag_chain if self.vector_store else self.default_chain
            response = chain.invoke(
                {"input": text},
                config={"configurable": {"session_id": session_id}}
            )
            # Handle both possible output formats
            if isinstance(response, dict):
                return response.get("answer", response.get("output", response.get("text", str(response))))
            return str(response)
        except Exception as e:
            return f"Error processing message: {str(e)}"

    def chat_stream(self, text: str, session_id: str = "default"):
        """Stream chat responses"""
        try:
            chain = self.rag_chain if self.vector_store else self.default_chain
            
            # Create an empty placeholder for the message
            message_placeholder = st.empty()
            full_response = ""

            # Stream the response
            for chunk in chain.stream(
                {"input": text},
                config={"configurable": {"session_id": session_id}}
            ):
                # Handle different types of chunks
                if hasattr(chunk, "content"):
                    # For ChatMessage objects
                    content = chunk.content
                elif isinstance(chunk, dict):
                    # For dictionary responses, try different keys
                    content = (
                        chunk.get("output", "") or
                        chunk.get("response", "") or
                        chunk.get("answer", "") or
                        chunk.get("text", "") or
                        ""
                    )
                    # If content is still empty but we have a non-empty dict, convert it to string
                    if not content and chunk:
                        content = str(chunk)
                else:
                    # For string or other types
                    content = str(chunk)
                
                if content and not content.startswith('{'):  # Avoid printing raw JSON
                    full_response += content
                    message_placeholder.markdown(full_response + "▌")

            # Final update without the cursor
            message_placeholder.markdown(full_response)
            return full_response

        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            st.error(error_msg)
            return error_msg

    def reset(self, session_id: str = "default"):
        """Reset the conversation state for a session"""
        if session_id in self.store:
            del self.store[session_id]
