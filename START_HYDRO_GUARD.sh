#!/usr/bin/env bash
echo "======================================================================"
echo "  HYDRO-GUARD AI : Urban Drainage, Flood & Water Quality System"
echo "======================================================================"
echo ""

echo "Checking / installing requirements..."
pip install -r requirements.txt
echo ""

echo "Starting HYDRO-GUARD AI servers..."
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
FASTAPI_PID=$!

python -m streamlit run frontend/app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false &
STREAMLIT_PID=$!

echo ""
echo "======================================================================"
echo "  ALL SERVICES STARTED!"
echo "  * Main Web Application: http://127.0.0.1:8000/"
echo "  * Indore Flood Map:     http://127.0.0.1:8000/#map"
echo "  * Streamlit Analytics:  http://localhost:8501/"
echo "======================================================================"
echo "Press Ctrl+C to stop both servers."

trap "kill $FASTAPI_PID $STREAMLIT_PID 2>/dev/null; exit" SIGINT SIGTERM
wait

