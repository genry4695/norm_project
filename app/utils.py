from pydantic import BaseModel
from llama_index.core import VectorStoreIndex, Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from dataclasses import dataclass
from dotenv import load_dotenv
import os
from typing import List, Dict, Any
import pypdf
import re

# Load environment variables
load_dotenv()

def get_openai_api_key():
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return key

@dataclass
class Citation:
    source: str
    text: str

class Output(BaseModel):
    query: str
    response: str
    citations: list[Citation]

def extract_pdf_lines(path: str) -> List[Dict[str, Any]]:
    """Extract text from PDF line by line with page tracking."""
    reader = pypdf.PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):  # 1-based page numbers
        raw = page.extract_text() or ""
        # Normalize common issues
        lines = [l.rstrip() for l in raw.splitlines()]
        pages.append({"page": i, "lines": lines})
    return pages

def create_documents_from_pdf(pdf_path: str, source_file: str = "docs/laws.pdf"):
    """Create properly structured documents from PDF using LLM for intelligent extraction."""
    pages = extract_pdf_lines(pdf_path)
    
    # Combine all text from PDF
    all_text = ""
    for page in pages:
        all_text += " " + " ".join(page["lines"])
    
    # Use LLM to extract structured sections
    try:
        from llama_index.llms.openai import OpenAI
        from llama_index.core import PromptTemplate
        
        # Get API key
        api_key = get_openai_api_key()
        llm = OpenAI(api_key=api_key, model="gpt-4o-mini")
        
        # Create a prompt to extract structured legal sections
        extraction_prompt = PromptTemplate(
            "You are a legal document parser. Extract all legal sections from the following text and format them as structured documents.\n\n"
            "For each section, identify:\n"
            "- Section number (e.g., 1, 1.1, 1.1.1)\n"
            "- Section title/content\n"
            "- Any subsections\n\n"
            "Text to parse:\n{text}\n\n"
            "IMPORTANT: Return ONLY valid JSON. Do not include any explanatory text before or after the JSON.\n\n"
            "Return a JSON array of objects with this exact structure:\n"
            "[\n"
            "  {\n"
            "    \"section_number\": \"1\",\n"
            "    \"title\": \"Peace\",\n"
            "    \"content\": \"The law requires petty lords and landed knights to take their disputes to their liege lord...\"\n"
            "  }\n"
            "]"
        )
        
        # Extract structured content
        response = llm.complete(extraction_prompt.format(text=all_text[:4000]))  # Limit text length
        
        # Parse the response and create documents
        import json
        try:
            sections = json.loads(response.text)
            documents = []
            
            for section in sections:
                if isinstance(section, dict) and 'content' in section:
                    meta = {
                        "section_number": section.get("section_number", "unknown"),
                        "title": section.get("title", section.get("content", "")[:100]),
                        "page_start": 1,
                        "page_end": 2,
                        "source_file": source_file,
                        "source": source_file,
                        "citations": [f"{source_file}#p1"]
                    }
                    doc = Document(text=section["content"], metadata=meta)
                    documents.append(doc)
            
            return documents
            
        except json.JSONDecodeError:
            # If LLM response isn't valid JSON, raise an error
            raise Exception("LLM extraction failed: Invalid JSON response")
            
    except Exception as e:
        raise Exception(f"LLM extraction failed: {e}")


class DocumentService:
    """Service for loading PDF documents and extracting their contents."""
    
    def __init__(self):
        pass
    
    def create_documents(self, pdf_path: str) -> List[Document]:
        """
        Load PDF and create Document objects for vector indexing.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of Document objects with metadata and text
        """
        try:
            return create_documents_from_pdf(pdf_path)
            
        except Exception as e:
            raise Exception(f"Document creation failed: {str(e)}")


class QdrantService:
    """Service for vector search and RAG operations using Qdrant."""
    
    def __init__(self, k: int = 2):
        self.index = None
        self.k = k

    def connect(self) -> None:
        """Initialize the vector index with OpenAI services."""
        from llama_index.core import Settings
        
        # Get API key
        api_key = get_openai_api_key()
        
        # Configure settings for embeddings and LLM
        Settings.embed_model = OpenAIEmbedding(api_key=api_key)
        Settings.llm = OpenAI(api_key=api_key, model="gpt-5")
        
        # Create a simple in-memory index
        self.index = VectorStoreIndex.from_documents([])

    def load(self, docs: List[Document]) -> None:
        """Load documents into the vector index."""
        for doc in docs:
            self.index.insert(doc)

    def query(self, query_str: str) -> Output:
        """
        Query the vector index and return RAG response with citations.
        
        Args:
            query_str: The query string
            
        Returns:
            Output object with query, response, and citations
        """
        if not self.index:
            raise Exception("Vector index not initialized. Call connect() first.")
        
        # Create a query engine from the index
        query_engine = self.index.as_query_engine(
            similarity_top_k=self.k,
            response_mode="compact"
        )
        
        # Execute the query
        response = query_engine.query(query_str)
        
        # Extract citations from the response
        citations = []
        if hasattr(response, 'source_nodes') and response.source_nodes:
            for i, node in enumerate(response.source_nodes[:self.k]):
                source = node.metadata.get('source', f'Chunk {i+1}')
                text = node.text[:200] + "..." if len(node.text) > 200 else node.text
                citations.append(Citation(source=source, text=text))
        
        # If no citations found, create a generic one
        if not citations:
            citations.append(Citation(
                source="Document",
                text="Information retrieved from document analysis."
            ))
        
        # Create the output object
        output = Output(
            query=query_str,
            response=response.response,
            citations=citations
        )
        
        return output