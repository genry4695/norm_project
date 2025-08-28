# Norm AI - Westeros Legal Compliance System

A FastAPI-based legal compliance system that allows natural language queries of Game of Thrones laws using AI-powered document extraction and vector search.

## Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key

### Setup
```bash
# Clone and setup
cd norm_project
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Add your OpenAI API key
echo "OPENAI_API_KEY=your_key_here" > .env
```

### Run
```bash
# Start the service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or with Docker
docker build -t norm-project .
docker run -p 8000:8000 --env-file .env norm-project
```

## API Usage

### Query Endpoint
```
GET /query?query={your_question}
```

**Examples:**
- `What does law 3.1.1 say about widow maintenance?`
- `How do trials work in the Seven Kingdoms?`
- `What are the rules for the Night's Watch?`

**Response:**
```json
{
  "query": "What does law 3.1.1 say about widow maintenance?",
  "response": "The law requires the heir to maintain their father's surviving widow...",
  "citations": [
    {
      "source": "Law 3.1.1 (Widows) - Maintenance of Widow",
      "text": "However, the law requires the heir to maintain..."
    }
  ]
}
```

## Access
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs (Swagger UI)

## Features
- AI-powered PDF text extraction and structuring
- Vector similarity search with OpenAI embeddings
- Rich citations including law numbers and categories
- FastAPI with automatic API documentation
- Docker support for production deployment

## Testing
```bash
# Test the system
python -c "from app.utils import DocumentService; ds = DocumentService(); docs = ds.create_documents('docs/laws.pdf'); print(f'Created {len(docs)} documents')"
```
