from fastapi import FastAPI, Query
from app.utils import Output, DocumentService, QdrantService

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "API is running"}

@app.get("/query")
async def query_documents(query: str = Query(..., description="Query string to search documents")):
    try:
        doc_service = DocumentService()
        qdrant_service = QdrantService(k=2)
        
        pdf_path = "docs/laws.pdf"
        documents = doc_service.create_documents(pdf_path)
        
        if not documents:
            return Output(
                query=query,
                response="No documents found to search through.",
                citations=[]
            )
        
        qdrant_service.connect()
        qdrant_service.load(documents)
        
        result = qdrant_service.query(query)
        
        return result
        
    except Exception as e:
        return Output(
            query=query,
            response=f"Error processing query: {str(e)}",
            citations=[]
        )