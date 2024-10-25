import chromadb
from chromadb.config import Settings
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
import os

def init_chroma():
    # Create a new ChromaDB client
    client = chromadb.PersistentClient(
        path="./chroma_db",
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )

    # Create a collection
    collection = client.get_or_create_collection(
        name="knowledge_base",
        metadata={"hnsw:space": "cosine"}
    )

    # Add some initial test documents to verify the setup
    test_docs = [
        "This is a test document to verify ChromaDB setup.",
        "Another test document to ensure proper initialization.",
    ]

    collection.add(
        documents=test_docs,
        metadatas=[{"source": "test"} for _ in test_docs],
        ids=[f"test_{i}" for i in range(len(test_docs))]
    )

    # Test query to verify everything works
    results = collection.query(
        query_texts=["test document"],
        n_results=1
    )

    print("ChromaDB initialized successfully!")
    print(f"Test query results: {results}")

if __name__ == "__main__":
    init_chroma()