import streamlit as st
from typing import List, Dict, Any, Optional
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

import streamlit as st
from typing import List, Dict, Any, Optional
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, TextLoader
import tempfile
import os

class LMMentorBot:
    def __init__(self):
        try:
            self.openai_key = st.secrets["OPENAI_KEY"]
            self.chat = ChatOpenAI(
                temperature=0.7,
                model_name="gpt-4",
                openai_api_key=self.openai_key
            )
            self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_key)
        except KeyError:
            st.error("OpenAI API key not found in secrets. Please add it to your Streamlit secrets.")
            st.stop()

        self.conversation_history = []
        self.learning_stage = "initial"
        self.uploaded_file_content = None
        self.vector_store = None
        
    def upload_file(self, uploaded_file) -> str:
        """Process uploaded file and create vector store for context"""
        if uploaded_file is None:
            return "No file uploaded."
        
        try:
            # Create a temporary directory to store the file
            with tempfile.TemporaryDirectory() as temp_dir:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                
                # Save uploaded file to temporary directory
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                # Load and process the file based on its type
                if uploaded_file.name.endswith('.pdf'):
                    loader = PyPDFLoader(file_path)
                    documents = loader.load()
                elif uploaded_file.name.endswith('.txt'):
                    loader = TextLoader(file_path)
                    documents = loader.load()
                else:
                    return "Unsupported file type. Please upload a PDF or text file."

                # Split documents into chunks
                text_splitter = CharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    length_function=len
                )
                splits = text_splitter.split_documents(documents)

                # Create vector store
                self.vector_store = Chroma.from_documents(
                    documents=splits,
                    embedding=self.embeddings,
                    persist_directory="./chroma_db"
                )

                return f"Successfully processed {uploaded_file.name}. You can now ask questions about its content."

        except Exception as e:
            return f"Error processing file: {str(e)}"

    def process_query(self, user_input: str) -> str:
        """Process user input and determine appropriate response strategy"""
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # If we have a vector store, search for relevant context
        relevant_context = ""
        if self.vector_store:
            search_results = self.vector_store.similarity_search(user_input, k=3)
            relevant_context = "\n".join([doc.page_content for doc in search_results])
        
        # Detect if the query is a code request
        if self._is_code_request(user_input):
            response = self._handle_code_request(user_input, relevant_context)
        else:
            response = self._generate_socratic_response(user_input, relevant_context)

        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def _generate_socratic_response(self, query: str, context: str = "") -> str:
        """Generate a response using the Socratic method"""
        system_prompt = """You are TARA, a Technical Assistant for Responsible AI learning. 
        Using the Socratic method:
        1. Ask thought-provoking questions related to the query
        2. Guide the student towards discovering the answer
        3. Encourage critical thinking and self-reflection
        4. Break down complex concepts into manageable parts
        
        If context is provided, use it to inform your response while maintaining the Socratic approach."""

        messages = [
            SystemMessage(content=system_prompt),
            SystemMessage(content=f"Context from uploaded documents:\n{context}" if context else "No additional context provided."),
            HumanMessage(content=query)
        ]

        response = self.chat(messages)
        return response.content

    def _handle_code_request(self, query: str, context: str = "") -> str:
        """Handle code-related queries with an educational approach"""
        if self.learning_stage == "initial":
            return self._generate_initial_guidance(query, context)
        elif self.learning_stage == "planning":
            return self._review_user_plan(query, context)
        elif self.learning_stage == "implementation":
            return self._provide_implementation_guidance(query, context)
        else:  # review
            return self._review_code_understanding(query, context)

    # Update other methods to include context parameter
    def _generate_initial_guidance(self, query: str, context: str = "") -> str:
        system_prompt = """You are TARA, a Technical Assistant for Responsible AI learning. 
        When responding to code requests:
        1. Reference any relevant information from the uploaded documents
        2. Acknowledge the request
        3. Explain why it's important to understand the concepts first
        4. Encourage the user to try planning their solution
        5. Ask them to write pseudo-code or describe their approach
        6. Offer to break down the problem into smaller steps
        
        Use a friendly, encouraging tone while maintaining educational value."""

        messages = [
            SystemMessage(content=system_prompt),
            SystemMessage(content=f"Context from uploaded documents:\n{context}" if context else "No additional context provided."),
            HumanMessage(content=f"User is requesting code for: {query}")
        ]

        response = self.chat(messages)
        self.learning_stage = "planning"
        return response.content

    def reset(self):
        """Reset the conversation state"""
        self.conversation_history = []
        self.learning_stage = "initial"
        self.uploaded_file_content = None
        self.vector_store = None
 
    def process_query(self, user_input: str) -> str:
        """Process user input and determine appropriate response strategy"""
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Detect if the query is a code request
        if self._is_code_request(user_input):
            response = self._handle_code_request(user_input)
        else:
            response = self._generate_socratic_response(user_input)

        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def _is_code_request(self, query: str) -> bool:
        """Detect if the query is asking for code"""
        code_indicators = [
            "code", "example", "implement", "write", "create", "build",
            "how to make", "develop", "script", "program", "function",
            "class", "style", "css", "html", "javascript", "python"
        ]
        return any(indicator in query.lower() for indicator in code_indicators)

    def _handle_code_request(self, query: str) -> str:
        """Handle code-related queries with an educational approach"""
        if self.learning_stage == "initial":
            return self._generate_initial_guidance(query)
        elif self.learning_stage == "planning":
            return self._review_user_plan(query)
        elif self.learning_stage == "implementation":
            return self._provide_implementation_guidance(query)
        else:  # review
            return self._review_code_understanding(query)

    def _generate_initial_guidance(self, query: str) -> str:
        """Generate initial guidance for code requests"""
        system_prompt = """You are TARA, a Technical Assistant for Responsible AI learning. 
        When responding to code requests:
        1. Acknowledge the request
        2. Explain why it's important to understand the concepts first
        3. Encourage the user to try planning their solution
        4. Ask them to write pseudo-code or describe their approach
        5. Offer to break down the problem into smaller steps
        6. Remind them that while AI can provide code, understanding is crucial for learning
        
        Use a friendly, encouraging tone while maintaining educational value."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User is requesting code for: {query}")
        ]

        response = self.chat(messages)
        self.learning_stage = "planning"
        return response.content

    def _review_user_plan(self, user_input: str) -> str:
        """Review user's planned approach and provide feedback"""
        system_prompt = """Review the user's approach and:
        1. Acknowledge their effort
        2. Point out good aspects of their plan
        3. Identify potential improvements
        4. Ask guiding questions about missing considerations
        5. Offer suggestions for better approaches if needed
        
        If they haven't provided a plan, gently remind them to share their thoughts first."""

        messages = [
            SystemMessage(content=system_prompt),
            *[HumanMessage(content=m["content"]) if m["role"] == "user" else 
              AIMessage(content=m["content"]) for m in self.conversation_history[-3:]]
        ]

        response = self.chat(messages)
        
        # If user has provided a reasonable plan, move to implementation
        if "pseudo" in user_input.lower() or "plan" in user_input.lower():
            self.learning_stage = "implementation"
        
        return response.content

    def _provide_implementation_guidance(self, query: str) -> str:
        """Provide implementation guidance with explanations"""
        system_prompt = """Provide code guidance by:
        1. Showing a basic implementation
        2. Explaining each part of the code
        3. Asking the user to explain how certain parts work
        4. Suggesting modifications they can try
        5. Providing resources for further learning
        
        Include comments in the code to aid understanding."""

        messages = [
            SystemMessage(content=system_prompt),
            *[HumanMessage(content=m["content"]) if m["role"] == "user" else 
              AIMessage(content=m["content"]) for m in self.conversation_history[-3:]]
        ]

        response = self.chat(messages)
        self.learning_stage = "review"
        return response.content

    def _review_code_understanding(self, user_input: str) -> str:
        """Review user's understanding of the code"""
        system_prompt = """Check understanding by:
        1. Asking specific questions about the code
        2. Encouraging modifications and experimentation
        3. Suggesting additional features they could add
        4. Providing tips for best practices
        5. Offering resources for deeper learning
        
        Maintain a supportive tone while ensuring learning objectives are met."""

        messages = [
            SystemMessage(content=system_prompt),
            *[HumanMessage(content=m["content"]) if m["role"] == "user" else 
              AIMessage(content=m["content"]) for m in self.conversation_history[-3:]]
        ]

        response = self.chat(messages)
        self.learning_stage = "initial"  # Reset for next interaction
        return response.content

    def _generate_socratic_response(self, query: str) -> str:
        """Generate a response using the Socratic method for non-code queries"""
        system_prompt = """Using the Socratic method:
        1. Ask thought-provoking questions related to the query
        2. Guide the student towards discovering the answer
        3. Encourage critical thinking and self-reflection
        4. Break down complex concepts into manageable parts"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]

        response = self.chat(messages)
        return response.content

    def reset(self):
        """Reset the conversation state"""
        self.conversation_history = []
        self.learning_stage = "initial"