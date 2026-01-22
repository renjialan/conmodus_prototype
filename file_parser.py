import os
import tempfile
from typing import Optional, Union, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader, 
    TextLoader,
    UnstructuredMarkdownLoader,
    CSVLoader,
    PythonLoader
)
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pypdf import PdfReader

class FileParser:
    def __init__(self, google_api_key: str):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=google_api_key
        )
        # Specific splitter for educational materials
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
            keep_separator=True
        )
    
    def extract_structured_pdf(self, uploaded_file) -> str:
        """
        Extract text from PDFs while preserving structure important for educational materials
        """
        try:
            reader = PdfReader(uploaded_file)
            structured_text = []
            
            for page in reader.pages:
                # Use layout-preserved text extraction
                text = page.extract_text(extraction_mode='layout')
                
                # Preserve section headers and formatting
                lines = text.split('\n')
                formatted_lines = []
                for line in lines:
                    # Preserve bullet points and numbering
                    if line.strip().startswith(('•', '-', '*', '1.', '2.', '3.')):
                        formatted_lines.append('\n' + line)
                    # Preserve section headers (assuming they're in caps or followed by :)
                    elif line.isupper() or ':' in line:
                        formatted_lines.append('\n\n' + line + '\n')
                    else:
                        formatted_lines.append(line)
                
                structured_text.append(' '.join(formatted_lines))
            
            return '\n'.join(structured_text)

        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")

    def process_test_cases(self, file_path: str) -> str:
        """
        Special handling for Python test case files
        """
        try:
            with open(file_path, 'r') as file:
                content = file.read()
                
            # Preserve test case structure and comments
            lines = content.split('\n')
            formatted_lines = []
            in_test_case = False
            
            for line in lines:
                if line.startswith('def test_'):
                    in_test_case = True
                    formatted_lines.append('\n' + line)
                elif line.startswith('    ') and in_test_case:
                    formatted_lines.append(line)
                elif line.strip() == '':
                    in_test_case = False
                    formatted_lines.append(line)
                else:
                    formatted_lines.append(line)
            
            return '\n'.join(formatted_lines)
        except Exception as e:
            raise Exception(f"Error processing test cases: {str(e)}")

    def parse_file(self, uploaded_file) -> Union[Chroma, None]:
        """Process uploaded file and create vector store for context"""
        if uploaded_file is None:
            return None
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                
                # Initialize documents list
                documents = []
                
                # Process different file types
                if file_extension == '.pdf':
                    text = self.extract_structured_pdf(uploaded_file)
                    documents = self.text_splitter.create_documents(
                        [text],
                        metadatas=[{"source": uploaded_file.name}]  # Add metadata
                    )
                
                elif file_extension in ['.py', '.txt', '.md', '.csv']:
                    loader_class = {
                        '.py': PythonLoader,
                        '.txt': TextLoader,
                        '.md': UnstructuredMarkdownLoader,
                        '.csv': CSVLoader
                    }[file_extension]
                    
                    loader = loader_class(file_path)
                    raw_documents = loader.load()
                    documents = self.text_splitter.split_documents(raw_documents)
                    
                    # Add metadata to each document
                    for doc in documents:
                        doc.metadata["source"] = uploaded_file.name
                
                else:
                    raise ValueError("Unsupported file type. Please upload a PDF, Python, Markdown, TXT, or CSV file.")

                if not documents:
                    raise ValueError("No content could be extracted from the file.")

                # Create and return vector store
                return Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings
                )

        except Exception as e:
            raise Exception(f"Error processing file: {str(e)}")

    def get_metadata(self, file_path: str) -> Dict:
        """Extract metadata about the educational material"""
        try:
            file_name = os.path.basename(file_path)
            file_type = os.path.splitext(file_name)[1].lower()
            
            metadata = {
                "file_name": file_name,
                "file_type": file_type,
                "material_type": self._determine_material_type(file_name),
            }
            
            return metadata
        except Exception as e:
            return {"error": str(e)}

    def _determine_material_type(self, file_name: str) -> str:
        """Determine the type of educational material based on filename"""
        file_name_lower = file_name.lower()
        
        if any(term in file_name_lower for term in ['rubric', 'grading', 'criteria']):
            return 'rubric'
        elif any(term in file_name_lower for term in ['test', 'spec', 'case']):
            return 'test_cases'
        elif any(term in file_name_lower for term in ['assign', 'hw', 'project']):
            return 'assignment'
        else:
            return 'general'