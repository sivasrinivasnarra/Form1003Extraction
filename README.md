# FormsiQ: Intelligent Form Field Extractor

An AI-powered solution for extracting fields from mortgage transcripts using Gemini-1.5-Pro.

## Features
- Automated field extraction from transcripts
- Real-time processing with confidence scores
- User-friendly Streamlit interface
- RESTful API endpoints

## Prerequisites
- Docker and Docker Compose
- Google API Key for Gemini AI

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd formsiq_project
```

2. Set up environment variables:
```bash
# Create .env file
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

3. Run with Docker Compose:
```bash
docker-compose up --build
```

4. Access the application:
- Streamlit UI: http://localhost:8501
- API Endpoint: http://localhost:8000/extract-fields

## API Usage

Extract fields from a transcript:
```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"transcript":"Your transcript text here"}' \
     http://localhost:8000/extract-fields
```

## Kubernetes Deployment (Optional)

1. Create Kubernetes secrets:
```bash
kubectl create secret generic formsiq-secrets \
  --from-literal=GOOGLE_API_KEY=your_api_key_here
```

2. Apply Kubernetes manifests:
```bash
kubectl apply -f k8s/
```

## Development

Running locally without Docker:

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the Flask API:
```bash
python -m flask run --port=8000
```

3. Start Streamlit:
```bash
streamlit run ui/streamlit_app.py
```

## Architecture

- Frontend: Streamlit
- Backend: Flask + Python 3.9+
- AI: Google Gemini-1.5-Pro
- Containerization: Docker
- Orchestration: Docker Compose/Kubernetes

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Your chosen license]
