import sys
from typing import Dict, List, Any, Optional, AsyncGenerator
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import tempfile
import os

class LMMentorBot:
    def __init__(self):
        try:
            # Initialize API keys and environment variables
            self.openai_key = st.secrets["OPENAI_KEY"]
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
            os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN_API_KEY"]

            # Initialize core components
            self.llm = ChatOpenAI(
                temperature=0.7,
                model_name="gpt-4",
                openai_api_key=self.openai_key,
                streaming=True
            )
            self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_key)
            
        except KeyError:
            st.error("Required API keys not found in secrets. Please add them to your Streamlit secrets.")
            st.stop()

        # Initialize storage and state
        self.store = {}
        self.vector_store = None
        self.setup_rag_chain()

    def setup_rag_chain(self):
        """Set up the RAG chain with prompts and retrievers"""
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
        ])

        # Set up history-aware retriever if vector store exists
        if self.vector_store:
            history_aware_retriever = create_history_aware_retriever(
                self.llm,
                self.vector_store.as_retriever(),
                retriever_template
            )
            
            # Create RAG chain
            document_chain = create_stuff_documents_chain(self.llm, mentor_template)
            self.rag_chain = create_retrieval_chain(history_aware_retriever, document_chain)
            
            # Set up conversation history management
            self.conversational_rag_chain = RunnableWithMessageHistory(
                self.rag_chain,
                self.get_session_history,
                input_messages_key="input",
                history_messages_key="chat_history",
                output_messages_key="answer",
            )

    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """Get or create chat history for a session"""
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]

    def upload_file(self, uploaded_file) -> str:
        """Process uploaded file and create vector store for context"""
        if uploaded_file is None:
            return "No file uploaded."
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                
                # Save uploaded file
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                # Load and process file based on type
                if uploaded_file.name.endswith('.pdf'):
                    loader = PyPDFLoader(file_path)
                elif uploaded_file.name.endswith('.txt'):
                    loader = TextLoader(file_path)
                else:
                    return "Unsupported file type. Please upload a PDF or text file."

                documents = loader.load()
                
                # Split documents
                text_splitter = CharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    length_function=len
                )
                splits = text_splitter.split_documents(documents)

                # Create vector store
                self.vector_store = Chroma.from_documents(
                    documents=splits,
                    embedding=self.embeddings
                )

                # Reinitialize RAG chain with new vector store
                self.setup_rag_chain()
                
                return f"Successfully processed {uploaded_file.name}. Ready for questions!"

        except Exception as e:
            return f"Error processing file: {str(e)}"

    def chat(self, text: str, session_id: str = "default") -> str:
        """Process a chat message and return response"""
        if not self.vector_store:
            return "Please upload a document first to enable context-aware responses."

        try:
            response = self.conversational_rag_chain.invoke(
                {"input": text},
                config={"configurable": {"session_id": session_id}}
            )
            return response["answer"]
        except Exception as e:
            return f"Error processing message: {str(e)}"

    def chat_stream(self, text: str, session_id: str = "default"):
        """Stream chat responses"""
        if not self.vector_store:
            yield "Please upload a document first to enable context-aware responses."
            return

        try:
            for chunk in self.conversational_rag_chain.stream(
                {"input": text},
                config={"configurable": {"session_id": session_id}}
            ):
                if 'answer' in chunk:
                    yield chunk["answer"]
        except Exception as e:
            yield f"Error processing message: {str(e)}"

    def reset(self, session_id: str = "default"):
        """Reset the conversation state for a session"""
        if session_id in self.store:
            del self.store[session_id]