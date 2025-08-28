# Norm AI - Westeros Legal Compliance System

A FastAPI-based legal compliance system with a React frontend that allows natural language queries of Game of Thrones laws using AI-powered document extraction and vector search.

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- OpenAI API key

### Backend Setup
```bash
# Clone and setup
cd norm_project
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Add your OpenAI API key
echo "OPENAI_API_KEY=your_key_here" > .env
```

### Frontend Setup
```bash
cd frontend
npm install
```

### Run
```bash
# Terminal 1: Start the backend
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start the frontend
cd frontend
npm run dev
```

## Usage

- **Frontend**: http://localhost:3000 (or 3001 if 3000 is busy)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Features
- AI-powered PDF text extraction and structuring
- Vector similarity search with OpenAI embeddings
- Chat interface for natural language queries
- Rich citations including law numbers and categories
- FastAPI backend with React frontend
