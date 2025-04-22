#!/bin/bash

# Start Flask API in background
python -m flask run --host=0.0.0.0 --port=8000 &

# Start Streamlit
streamlit run ui/streamlit_app.py --server.port=8501 --server.address=0.0.0.0 