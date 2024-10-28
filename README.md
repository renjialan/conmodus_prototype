# Conmodus Prototype

A prototype implementation of an AI-powered academic chatbot system using LangChain and ChromaDB.

## Current Status
This is a prototype/proof-of-concept version with basic chatbot functionality. Some features are partially implemented or in development.

## Features

### Implemented
- Basic chat interface
- LLM integration using LangChain
- Vector database storage using ChromaDB
- Prompt template system
- Basic document processing

### In Development
- Degree audit parsing
- Comprehensive academic planning
- Feedback collection system
- Course recommendation engine

## Tech Stack
- Python 3.9+
- LangChain
- ChromaDB
- FastAPI
- Streamlit (for UI)

## Requirements
```txt
langchain==0.2.11
chromadb==0.5.5
fastapi==0.111.1
streamlit==1.37.0
python-dotenv==1.0.1

Project Structure
conmodus_prototype/
├── dashboard.py          # Main application interface
├── prompts/
│   ├── tara_prompt.txt      # Main conversation prompt
│   └── retriever_prompt.txt # Query generation prompt
├── utils/
│   └── vector_store.py      # Vector database utilities
└── requirements.txt
Setup and Installation
Clone the repository:
bash
git clone https://github.com/renjialan/conmodus_prototype.git
cd conmodus_prototype
Create and activate a virtual environment:
bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:
bash
pip install -r requirements.txt
Set up environment variables: Create a .env file in the root directory with:
OPENAI_API_KEY=your_api_key_here
Run the application:
bash
streamlit run dashboard.py
Current Limitations
Basic chat functionality only
Limited degree audit processing
Feedback system not yet implemented
Course recommendations in development
Contributing
This is a prototype project. For major changes, please open an issue first to discuss what you would like to change.

