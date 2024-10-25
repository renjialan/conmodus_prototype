import chromadb
from chromadb.config import Settings
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_chroma import Chroma
import shutil
import os
import streamlit as st

def reset_chroma():
    try:
        # Check if chroma_db directory exists before trying to remove it
        if os.path.exists("./chroma_db"):
            shutil.rmtree("./chroma_db")
        print("Old database removed successfully.")

        # Create fresh directory
        os.makedirs("./chroma_db", exist_ok=True)
        print("New directory created successfully.")

        # Initialize ChromaDB client
        client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        print("ChromaDB client initialized.")

        # Initialize embeddings using Streamlit secrets
        embeddings = OpenAIEmbeddings(
            openai_api_key=st.secrets["OPENAI_API_KEY"]
        )
        print("Embeddings initialized.")

        # Create new Chroma instance
        store = Chroma(
            persist_directory="./chroma_db",
            collection_name="umich_fa2024",
            embedding_function=embeddings,
            client=client
        )
        print("ChromaDB successfully initialized!")
        return store
    except Exception as e:
        print(f"Error in reset_chroma: {str(e)}")
        return None

if __name__ == "__main__":
    reset_chroma()