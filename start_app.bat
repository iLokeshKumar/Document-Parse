@echo off
echo Starting Legal AI Tool...

:: Start Backend
echo Starting Backend Server...
start "Legal AI Backend" cmd /k "cd backend && .\.venv\Scripts\activate && uvicorn main:app --reload --port 8000"

:: Start Frontend
echo Starting Frontend Server...
start "Legal AI Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ===================================================
echo Servers are starting!
echo Backend will be at: http://localhost:8000
echo Frontend will be at: http://localhost:3000
echo.
echo Please wait a few moments for them to initialize.
echo ===================================================
pause
