@echo off
echo Starting Product Launch Planner Backend...

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Start the FastAPI application with uvicorn
echo Starting FastAPI server...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause 