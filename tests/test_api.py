import pytest
from api.app import app
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_extract_fields_valid_input(client):
    """Test with valid input"""
    data = {
        "transcript": "The borrower's name is John Doe and the loan amount is $250,000"
    }
    response = client.post('/extract-fields', 
                          json=data,
                          content_type='application/json')
    assert response.status_code == 200
    assert 'fields' in response.json

def test_extract_fields_invalid_input(client):
    """Test with invalid input"""
    data = {}  # Missing transcript
    response = client.post('/extract-fields', 
                          json=data,
                          content_type='application/json')
    assert response.status_code == 400
    assert 'error' in response.json

def test_extract_fields_empty_transcript(client):
    """Test with empty transcript"""
    data = {"transcript": ""}
    response = client.post('/extract-fields', 
                          json=data,
                          content_type='application/json')
    assert response.status_code == 200
    assert 'fields' in response.json
