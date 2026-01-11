# Quick Start Guide

## Prerequisites
- Python 3.11+ 
- Node.js 18+ and npm
- Groq API Key (get from https://console.groq.com/)

## Setup

### Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Ensure .env file exists with GROQ_API_KEY
# Example .env content:
# GROQ_API_KEY=your_api_key_here
# CHROMA_PERSIST_DIR=./chroma_db

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## Access

- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Note

Make sure your `.env` file in the `backend` directory contains:
- `GROQ_API_KEY=your_actual_api_key`
- Optionally: `CHROMA_PERSIST_DIR=./chroma_db`
