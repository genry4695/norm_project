from fastapi import FastAPI, Query
from app.utils import Output

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

"""
Please create an endpoint that accepts a query string, e.g., "what happens if I steal 
from the Sept?" and returns a JSON response serialized from the Pydantic Output class.
"""