---
description: how to run the full project
---
// turbo-all

Follow these steps to start the application:

### 1. Start the Backend
```sh
cd backend
../.venv/bin/python3 -m uvicorn main:app --port 8000 --reload
```

### 2. Start the Frontend
In a new terminal:
```sh
cd frontend
npm install
npm run dev
```

The application will be available at:
- **Frontend**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
