import streamlit as st
from typing import Optional, Dict
from langchain_openai import ChatOpenAI
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
            # Initialize API keys and environment variables
            self.openai_key = st.secrets["OPENAI_KEY"]
            self.setup_environment()
            
            # Initialize core components
            self.llm = ChatOpenAI(
                temperature=0.7,
                model_name="gpt-4",
                openai_api_key=self.openai_key,
                streaming=True,
                model_kwargs={"response_format": {"type": "text"}}
                
            )
            
            self.file_parser = FileParser(self.openai_key)
            
        except KeyError:
            st.error("Required API keys not found in secrets. Please add them to your Streamlit secrets.")
            st.stop()

        # Initialize storage and state
        self.store = {}
        self.vector_store = None
        
        # Load prompts
        self.retriever_prompt = self._load_prompt("prompts/retriever_prompt.txt")
        self.mentor_prompt = self._load_prompt("prompts/mentor_prompt.txt")
        # ADD THIS: Create a default template for non-RAG conversations
        self.default_template = ChatPromptTemplate.from_messages([
            ("system", self.mentor_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ])
        self.setup_rag_chain()
        self.setup_socratic_prompts()
        
        
        

    def _load_prompt(self, file_path: str) -> str:
        
            with open(file_path, "r") as f:
                return f.read()
        

    
    def setup_socratic_prompts(self):
        self.socratic_prompts = {
            "default": [
                "Before we dive into that, what do you already know about this topic?",
                "How do you think this concept might relate to other things you've learned?",
                "Can you think of any real-world applications for this idea?",
                "What aspects of this topic are you most curious about?"
            ]
        }
        self.socratic_index = {}

    
    def setup_rag_chain(self):
        """Set up the RAG chain with prompts and retrievers"""
        if not self.vector_store:
            return
        
        # Create prompt templates
        retriever_template = ChatPromptTemplate.from_messages([
            ("system", self.retriever_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])

        # MODIFIED: Update mentor template to handle context differently
        mentor_template = ChatPromptTemplate.from_messages([
            ("system", self.mentor_prompt),
            ("system", "Here is the relevant context: {context}"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        # Set up history-aware retriever
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}
        )
        retrieved_docs = retriever.get_relevant_documents("test input")
        print(f"Retrieved {len(retrieved_docs)} documents")  # Debugging line
        
        history_aware_retriever = create_history_aware_retriever(
            self.llm,
            retriever,
            retriever_template
        )
        
        # MODIFIED: Create document chain with specific configuration
        document_chain = create_stuff_documents_chain(
            llm=self.llm,
            prompt=mentor_template,
            document_variable_name="context",
        )
        
        # MODIFIED: Create retrieval chain with specific configuration
        self.rag_chain = create_retrieval_chain(
            retriever=history_aware_retriever,
            combine_docs_chain=document_chain,
            return_source_documents=True,
        )
        
        # MODIFIED: Update conversation chain configuration
        self.conversational_rag_chain = RunnableWithMessageHistory(
            runnable=self.rag_chain,
            message_history_provider=self.get_session_history,
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
                print(f"Vector store initialized: {self.vector_store is not None}")  # Debugging line
                # Reinitialize RAG chain with new vector store
                self.setup_rag_chain()
                return f"Successfully processed {uploaded_file.name}. Ready for context-aware responses!"
            return "No file uploaded."
        except Exception as e:
            return str(e)

    def chat(self, text: str, session_id: str = "default") -> str:
        """Process a chat message and return response"""
        try:
            if not self.vector_store:
                # Non-RAG conversation handling remains the same
                history = self.get_session_history(session_id)
                chain = self.default_template | self.llm
                response = chain.invoke({
                    "input": text,
                    "chat_history": history.messages
                })
                history.add_user_message(text)
                history.add_ai_message(response.content)
                return response.content
            
            # MODIFIED: RAG conversation handling
            history = self.get_session_history(session_id)
            
            # Prepare the input dictionary
            input_dict = {
                "input": text,
                "chat_history": history.messages,
            }
            print(f"Response structure: {response}")  # Debugging line
            # Get response from the RAG chain
            response = self.conversational_rag_chain.invoke(
                input_dict,
                config={"configurable": {"session_id": session_id}}
            )
            
            # Update conversation history
            history.add_user_message(text)
            if isinstance(response, dict) and "answer" in response:
                history.add_ai_message(response["answer"])
                return response["answer"]
            else:
                return str(response)
                
        except Exception as e:
            st.error(f"Error in chat processing: {str(e)}")
            return f"I encountered an error while processing your message. Please try again or reset the conversation."
    def chat_stream(self, text: str, session_id: str = "default"):
        """Stream chat responses"""
        try:
            if not self.vector_store:
                # Non-RAG streaming remains the same
                history = self.get_session_history(session_id)
                chain = self.default_template | self.llm
                for chunk in chain.stream({
                    "input": text,
                    "chat_history": history.messages
                }):
                    if hasattr(chunk, 'content'):
                        yield chunk.content
                history.add_user_message(text)
                history.add_ai_message("")
                return

            # MODIFIED: RAG streaming
            history = self.get_session_history(session_id)
            input_dict = {
                "input": text,
                "chat_history": history.messages,
            }
            
            for chunk in self.conversational_rag_chain.stream(
                input_dict,
                config={"configurable": {"session_id": session_id}}
            ):
                if isinstance(chunk, dict) and 'answer' in chunk:
                    yield chunk["answer"]
                elif hasattr(chunk, 'content'):
                    yield chunk.content
                
            history.add_user_message(text)
                        
        except Exception as e:
            yield f"Error processing message: {str(e)}"