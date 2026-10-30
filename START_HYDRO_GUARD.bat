@echo off
title HYDRO-GUARD AI Launcher
echo ======================================================================
echo   HYDRO-GUARD AI : Urban Drainage, Flood & Water Quality System
echo ======================================================================
echo.

REM Optional dependency install check
echo Checking / installing requirements...
pip install -r requirements.txt
echo.

echo Starting HYDRO-GUARD AI servers...
echo [1/2] Starting FastAPI Web App at http://127.0.0.1:8000 ...
start "HYDRO-GUARD AI - Web App (Port 8000)" cmd /k "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"

echo [2/2] Starting Streamlit Analytics Dashboard at http://localhost:8501 ...
start "HYDRO-GUARD AI - Streamlit Dashboard (Port 8501)" cmd /k "python -m streamlit run frontend/app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false"

echo.
echo ======================================================================
echo   ALL SERVICES STARTED!
echo   * Main Web Application: http://127.0.0.1:8000/
echo   * Indore Flood Map:     http://127.0.0.1:8000/#map
echo   * Streamlit Analytics:  http://localhost:8501/
echo ======================================================================
echo.
pause

