from fastapi import FastAPI, Query
from app.utils import Output, DocumentService, QdrantService

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "API is running"}

@app.get("/query")
async def query_documents(query: str = Query(..., description="Query string to search documents")):
    """
    Query documents using RAG (Retrieval-Augmented Generation).
    
    Args:
        query: The question or query string
        
    Returns:
        JSON response with query, response, and citations
    """
    try:
        # Initialize services
        doc_service = DocumentService()
        qdrant_service = QdrantService(k=2)
        
        # Load documents from the laws.pdf file
        pdf_path = "docs/laws.pdf"
        documents = doc_service.create_documents(pdf_path)
        
        if not documents:
            return Output(
                query=query,
                response="No documents found to search through.",
                citations=[]
            )
        
        # Connect and load documents into the vector index
        qdrant_service.connect()
        qdrant_service.load(documents)
        
        # Query the documents
        result = qdrant_service.query(query)
        
        return result
        
    except Exception as e:
        return Output(
            query=query,
            response=f"Error processing query: {str(e)}",
            citations=[]
        )