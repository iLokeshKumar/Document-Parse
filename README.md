# Legal AI Tool

A RAG-based Legal AI tool that answers questions from uploaded documents with citations.

## Prerequisites
- Python 3.10+
- Node.js 18+

## Setup

### 1. Backend
Navigate to the `backend` directory:
```bash
cd backend
```
Install dependencies:
```bash
pip install -r requirements.txt
```
Create a `.env` file (or rename `.env.example` if provided) and add your Gemini API Key:
```bash
GOOGLE_API_KEY=your_api_key_here
```

### 2. Frontend
Navigate to the `frontend` directory:
```bash
cd frontend
# Legal AI Tool

A RAG-based Legal AI tool that answers questions from uploaded documents with citations.

## Prerequisites
- Python 3.10+
- Node.js 18+

## Setup

### 1. Backend
Navigate to the `backend` directory:
```bash
cd backend
```
Install dependencies:
```bash
pip install -r requirements.txt
```
Create a `.env` file (or rename `.env.example` if provided) and add your Gemini API Key:
```bash
GOOGLE_API_KEY=your_api_key_here
```

### 2. Frontend
Navigate to the `frontend` directory:
```bash
cd frontend
```
Install dependencies:
```bash
npm install
```

## 🚀 How to Run

### Option 1: One-Click Start (Recommended)
Double-click the **`start_app.bat`** file in the `legal_ai` folder. This will open two terminal windows (one for backend, one for frontend).

### Option 2: Manual Start

**1. Start the Backend:**
Open a terminal in `legal_ai/backend` and run:
```bash
# Activate virtual environment
.\.venv\Scripts\activate

# Start server
uvicorn main:app --reload --port 8000
```

**2. Start the Frontend:**
Open a new terminal in `legal_ai/frontend` and run:
```bash
npm run dev
```

Access the app at: [http://localhost:3000](http://localhost:3000)

## Usage
1. Upload a legal document (PDF, Text).
2. Ask a question (e.g., "What is the termination clause?").
3. View the answer and citations.
