# Resumes Insight - AI-Powered Resume Evaluation System

An intelligent Applicant Tracking System (ATS) that uses RAG (Retrieval-Augmented Generation) with Groq AI to evaluate resumes against job descriptions.

## Features

- 📄 **PDF Resume Upload**: Backend PDF text extraction using PyPDF2
- 🤖 **AI-Powered Evaluation**: Uses Groq's LLaMA models for intelligent candidate evaluation
- 🔍 **RAG Pipeline**: Retrieval-Augmented Generation for context-aware analysis
- 📊 **Detailed Scoring**: Skills, experience, and education scoring with recommendations
- 🎯 **Vector Search**: ChromaDB for efficient resume search and retrieval
- 🚀 **FastAPI Backend**: Modern, async Python backend
- ⚛️ **React Frontend**: Modern React + TypeScript frontend

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Groq API** - Fast LLM inference
- **ChromaDB** - Vector database for embeddings
- **PyPDF2** - PDF text extraction
- **Uvicorn** - ASGI server

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Shadcn/ui** - UI components

## Prerequisites

- **Python 3.11+** (tested with 3.11, 3.12)
- **Node.js 18+** and npm (or bun)
- **Groq API Key** - Get one from [Groq Console](https://console.groq.com/)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd resumes-insight
```

### 2. Backend Setup

#### Create Virtual Environment

```bash
cd backend

# On macOS/Linux:
python3 -m venv venv
source venv/bin/activate

# On Windows:
python -m venv venv
venv\Scripts\activate
```

#### Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Groq API key
nano .env  # or use your preferred editor
```

Required environment variables:
```env
GROQ_API_KEY=your_groq_api_key_here
CHROMA_PERSIST_DIR=./chroma_db  # Optional, defaults to ./chroma_db
```

#### Run the Backend

```bash
# Development mode (with auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python main.py
```

The backend will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Development mode
npm run dev
```

The frontend will be available at `http://localhost:8080`

#### Frontend Environment Variables (Optional)

Create a `.env` file in the `frontend` directory if your backend runs on a different port:

```env
VITE_API_URL=http://localhost:8000
```

## Project Structure

```
resumes-insight/
├── backend/
│   ├── main.py              # FastAPI application and routes
│   ├── config.py            # Configuration and settings
│   ├── schemas.py           # Pydantic models
│   ├── pdf_extractor.py     # PDF text extraction
│   ├── rag_utils.py         # RAG pipeline and vector store
│   ├── evaluation.py        # Candidate evaluation logic
│   ├── utils.py             # Helper utilities
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment variables template
│   └── chroma_db/           # ChromaDB data directory (auto-created)
│
└── frontend/
    ├── src/
    │   ├── components/      # React components
    │   ├── pages/           # Page components
    │   ├── services/        # API service layer
    │   ├── types/           # TypeScript types
    │   └── App.tsx          # Main app component
    ├── package.json
    └── vite.config.ts
```

## API Endpoints

### Health Check
- `GET /` - Health check
- `GET /health` - Detailed health check

### Jobs
- `POST /api/v1/jobs` - Create a job description
- `GET /api/v1/jobs` - List all jobs
- `GET /api/v1/jobs/{job_id}` - Get job by ID
- `PUT /api/v1/jobs/{job_id}` - Update job
- `DELETE /api/v1/jobs/{job_id}` - Delete job

### PDF Extraction
- `POST /api/v1/extract-pdf` - Extract text from PDF file

### Resumes
- `POST /api/v1/jobs/{job_id}/resumes` - Upload single resume
- `POST /api/v1/jobs/{job_id}/resumes/bulk` - Upload multiple resumes
- `GET /api/v1/jobs/{job_id}/candidates` - List candidates for a job

### Evaluation
- `POST /api/v1/evaluate` - Evaluate candidates
- `GET /api/v1/jobs/{job_id}/evaluate` - Evaluate all candidates for a job
- `GET /api/v1/jobs/{job_id}/candidates/{candidate_id}/evaluate` - Evaluate single candidate

### Results
- `GET /api/v1/results/{job_id}` - Get evaluation results
- `GET /api/v1/results/{job_id}/top` - Get top N candidates
- `GET /api/v1/results/{job_id}/summary` - Get results summary

See full API documentation at `http://localhost:8000/docs`

## Usage

1. **Start the backend** (see Backend Setup above)
2. **Start the frontend** (see Frontend Setup above)
3. **Open the application** in your browser at `http://localhost:8080`
4. **Create a job description** with required skills and requirements
5. **Upload PDF resumes** - The system will extract text automatically
6. **Run evaluation** - The AI will score and rank candidates
7. **Review results** - See detailed analysis, scores, and recommendations

## Troubleshooting

### Backend Issues

#### ModuleNotFoundError
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

#### GROQ_API_KEY not configured
- Check that `.env` file exists in the `backend` directory
- Verify `GROQ_API_KEY` is set in `.env`
- Restart the server after changing `.env`

#### Port already in use
- Change the port: `uvicorn main:app --reload --port 8001`
- Update frontend `VITE_API_URL` accordingly

#### ChromaDB errors
- Delete `chroma_db` directory and restart (this will clear all data)
- Ensure write permissions in the backend directory

### Frontend Issues

#### Cannot connect to backend
- Verify backend is running on `http://localhost:8000`
- Check browser console for CORS errors
- Verify `VITE_API_URL` in frontend `.env` if using custom port

#### PDF extraction fails
- Ensure backend `/api/v1/extract-pdf` endpoint is working
- Check backend logs for errors
- Verify PDF file is not corrupted

### macOS Compatibility

This project avoids problematic packages on macOS 12/13:
- ✅ No `torch` or `sentence-transformers` (uses ChromaDB's default embeddings)
- ✅ No `chroma-hnswlib` (uses ChromaDB's built-in indexing)
- ✅ All dependencies are compatible with macOS 12/13

## Development

### Running Tests

```bash
# Backend tests (when available)
cd backend
pytest

# Frontend tests (when available)
cd frontend
npm test
```

### Code Style

```bash
# Backend - use black, flake8, or your preferred formatter
black backend/

# Frontend - use ESLint
cd frontend
npm run lint
```

## Security Notes

- ⚠️ Never commit `.env` files (they're in `.gitignore`)
- ⚠️ Never commit API keys or secrets
- ⚠️ Use environment variables for all sensitive configuration
- ⚠️ In production, use proper secrets management

## License

[Add your license here]

## Support

For issues and questions:
- Check the troubleshooting section above
- Review API documentation at `/docs`
- Check backend logs for detailed error messages

## Contributing

[Add contribution guidelines here]

## Docker Deployment (Optional)

### Using Docker Compose

1. **Set up environment variables:**

```bash
# Create .env file in project root
echo "GROQ_API_KEY=your_groq_api_key_here" > .env
```

2. **Build and run:**

```bash
docker-compose up -d
```

3. **Access the application:**

- Frontend: `http://localhost:8080`
- Backend: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

4. **View logs:**

```bash
docker-compose logs -f
```

5. **Stop services:**

```bash
docker-compose down
```

### Using Docker individually

#### Backend only:

```bash
cd backend
docker build -t resumes-insight-backend .
docker run -p 8000:8000 --env-file .env resumes-insight-backend
```

#### Frontend only:

```bash
cd frontend
docker build -t resumes-insight-frontend .
docker run -p 8080:80 resumes-insight-frontend
```
