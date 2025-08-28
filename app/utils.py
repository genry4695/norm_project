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
    reader = pypdf.PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        raw = page.extract_text() or ""
        lines = [l.rstrip() for l in raw.splitlines()]
        pages.append({"page": i, "lines": lines})
    return pages

def create_documents_from_pdf(pdf_path: str, source_file: str = "docs/laws.pdf"):
    pages = extract_pdf_lines(pdf_path)
    
    all_text = ""
    for page in pages:
        all_text += " " + " ".join(page["lines"])
    
    try:
        from llama_index.llms.openai import OpenAI
        from llama_index.core import PromptTemplate
        
        api_key = get_openai_api_key()
        llm = OpenAI(api_key=api_key, model="gpt-4o-mini")
        
        extraction_prompt = PromptTemplate(
            "You are a legal document parser. Extract the legal structure from the following text.\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "- Extract BOTH category headers (like '1', '2', '3') AND substantive laws (like 1.1, 1.1.1, 1.1.2, 2.1, etc.)\n"
            "- Category headers should have section_number like '1', '2', '3' and represent main topics\n"
            "- Laws should have section_number like '1.1', '1.1.1', '1.1.2' and represent specific legal provisions\n"
            "- Each section should be a separate document\n"
            "- This will allow us to map laws to their categories\n\n"
            "Text to parse:\n{text}\n\n"
            "IMPORTANT: Return ONLY valid JSON. Do not include any explanatory text before or after the JSON.\n\n"
            "Return a JSON array with both categories and laws:\n"
            "[\n"
            "  {\n"
            "    \"section_number\": \"1\",\n"
            "    \"title\": \"Peace\",\n"
            "    \"content\": \"Main category for peace-related laws...\"\n"
            "  },\n"
            "  {\n"
            "    \"section_number\": \"1.1\",\n"
            "    \"title\": \"Dispute Resolution\",\n"
            "    \"content\": \"The law requires petty lords and landed knights to take their disputes...\"\n"
            "  }\n"
            "]"
        )
        
        response = llm.complete(extraction_prompt.format(text=all_text[:4000]))
        
        import json
        try:
            sections = json.loads(response.text)
            documents = []
            
            categories = {}
            for section in sections:
                if isinstance(section, dict) and 'content' in section:
                    section_number = section.get("section_number", "unknown")
                    if len(section_number.split('.')) == 1:
                        categories[section_number] = section.get("title", "")
            
            for section in sections:
                if isinstance(section, dict) and 'content' in section:
                    section_number = section.get("section_number", "unknown")
                    content = section["content"]
                    title = section.get("title", content[:100])
                    
                    if len(section_number.split('.')) > 1:
                        parts = section_number.split('.')
                        parent_category = parts[0]
                        category_title = categories.get(parent_category, "")
                        
                        law_path = f"{category_title} > {section_number}"
                        
                        meta = {
                            "section_number": section_number,
                            "title": title,
                            "category": parent_category,
                            "category_title": category_title,
                            "law_path": law_path,
                            "source_file": source_file,
                            "citations": [f"{source_file}"]
                        }
                        doc = Document(text=content, metadata=meta)
                        documents.append(doc)
            
            return documents
            
        except json.JSONDecodeError:
            raise Exception("LLM extraction failed: Invalid JSON response")
            
    except Exception as e:
        raise Exception(f"LLM extraction failed: {e}")


class DocumentService:
    def __init__(self):
        pass
    
    def create_documents(self, pdf_path: str) -> List[Document]:
        try:
            return create_documents_from_pdf(pdf_path)
            
        except Exception as e:
            raise Exception(f"Document creation failed: {str(e)}")


class QdrantService:
    def __init__(self, k: int = 2):
        self.index = None
        self.k = k

    def connect(self) -> None:
        from llama_index.core import Settings
        
        api_key = get_openai_api_key()
        
        Settings.embed_model = OpenAIEmbedding(api_key=api_key)
        Settings.llm = OpenAI(api_key=api_key, model="gpt-5")
        
        self.index = VectorStoreIndex.from_documents([])

    def load(self, docs: List[Document]) -> None:
        for doc in docs:
            self.index.insert(doc)

    def query(self, query_str: str) -> Output:
        if not self.index:
            raise Exception("Vector index not initialized. Call connect() first.")
        
        query_engine = self.index.as_query_engine(
            similarity_top_k=self.k,
            response_mode="compact"
        )
        
        response = query_engine.query(query_str)
        
        citations = []
        if hasattr(response, 'source_nodes') and response.source_nodes:
            for i, node in enumerate(response.source_nodes[:self.k]):
                section_number = node.metadata.get('section_number', 'Unknown')
                category_title = node.metadata.get('category_title', '')
                title = node.metadata.get('title', '')
                
                if category_title and section_number:
                    source = f"Law {section_number} ({category_title}) - {title}"
                elif section_number:
                    source = f"Law {section_number} - {title}"
                else:
                    source = f"Chunk {i+1}"
                
                text = node.text[:200] + "..." if len(node.text) > 200 else node.text
                citations.append(Citation(source=source, text=text))
        
        if not citations:
            citations.append(Citation(
                source="Document",
                text="Information retrieved from document analysis."
            ))
        
        output = Output(
            query=query_str,
            response=response.response,
            citations=citations
        )
        
        return output