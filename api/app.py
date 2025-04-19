from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os
import re
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# Configure Gemini AI
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("No API key found in .env file")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

def calculate_confidence(field_name, value, transcript):
    """
    Calculate confidence score based on various factors:
    1. Pattern matching strength
    2. Context clarity
    3. Format validity
    4. Presence of competing values
    """
    confidence = 0.5  # Base confidence
    
    # Pattern matching rules for each field
    patterns = {
        "Borrower Name": {
            'prefix_patterns': [
                r"borrower(?:'s)?\s+name\s+is\b",
                r"speaking\s+with\b",
                r"\b(?:mr|mrs|ms|dr)\.\s+",
                r"applicant:\s*",
            ],
            'format_pattern': r'^[A-Za-z\s\.-]+$',
            'competing': r'\b(?:name|called|named)\b'
        },
        "Loan Amount": {
            'prefix_patterns': [
                r"loan\s+(?:amount|of|for)\s+",
                r"requesting\s+(?:a\s+)?(?:loan\s+)?(?:of\s+)?\$?",
                r"borrow(?:ing)?\s+",
            ],
            'format_pattern': r'^\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?$',
            'competing': r'\b(?:income|salary|payment)\b'
        },
        "Property Address": {
            'prefix_patterns': [
                r"(?:property|address|located)\s+(?:at|is)\s+",
                r"looking\s+at\s+",
            ],
            'format_pattern': r'^\d+\s+[A-Za-z0-9\s,\.]+$',
            'competing': r'\b(?:address|location|property)\b'
        },
        "Annual Income": {
            'prefix_patterns': [
                r"(?:annual|yearly)\s+income\s+(?:is|of)\s+",
                r"makes\s+",
                r"earning\s+",
            ],
            'format_pattern': r'^\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?$',
            'competing': r'\b(?:income|salary|earning|makes)\b'
        }
    }
    
    field_patterns = patterns.get(field_name, {})
    
    # Check for strong prefix matches
    for prefix in field_patterns.get('prefix_patterns', []):
        if re.search(prefix, transcript, re.IGNORECASE):
            confidence += 0.2
            break
    
    # Check value format
    if field_patterns.get('format_pattern'):
        if re.match(field_patterns['format_pattern'], value.strip()):
            confidence += 0.15
    
    # Check for competing values
    if field_patterns.get('competing'):
        competing_count = len(re.findall(field_patterns['competing'], transcript, re.IGNORECASE))
        if competing_count > 1:
            confidence -= 0.1 * (competing_count - 1)
    
    # Context clarity (check for nearby relevant terms)
    context_window = 50
    value_pos = transcript.find(value)
    if value_pos != -1:
        context = transcript[max(0, value_pos - context_window):
                           min(len(transcript), value_pos + len(value) + context_window)]
        if field_patterns.get('competing') and re.search(field_patterns['competing'], context, re.IGNORECASE):
            confidence += 0.15
    
    # Adjust for special cases
    if field_name == "Borrower Name":
        # Lower confidence if multiple names found
        name_count = len(re.findall(r'\b(?:mr|mrs|ms|dr)\.\s+[a-z]+', transcript, re.IGNORECASE))
        if name_count > 1:
            confidence -= 0.1 * (name_count - 1)
    
    elif field_name == "Loan Amount":
        # Check for currency symbol and proper formatting
        if re.match(r'^\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?$', value):
            confidence += 0.1
    
    # Ensure confidence stays within 0-1 range
    return round(min(max(confidence, 0.0), 1.0), 2)

def extract_fields_with_gemini(transcript):
    try:
        prompt = f"""
        Extract these specific fields from the mortgage application transcript.
        Return only the raw extracted values without confidence scores.
        
        Transcript: {transcript}
        
        Required fields:
        - Borrower Name
        - Loan Amount
        - Property Address
        - Annual Income
        
        Format each line exactly as:
        Field: Value
        """

        print("Sending prompt to Gemini...")
        response = model.generate_content(prompt)
        print(f"Received response: {response.text}")

        # Process the response and calculate confidence scores
        fields = []
        for line in response.text.split('\n'):
            line = line.strip()
            if ':' in line:
                try:
                    field_name, value = [x.strip() for x in line.split(':', 1)]
                    
                    # Calculate confidence score based on various factors
                    confidence = calculate_confidence(field_name, value, transcript)
                    
                    fields.append({
                        "field_name": field_name,
                        "field_value": value,
                        "confidence_score": confidence
                    })
                except Exception as e:
                    print(f"Error processing line '{line}': {str(e)}")

        print(f"Processed fields with calculated confidence: {fields}")
        return {"fields": fields}

    except Exception as e:
        print(f"Extraction error: {str(e)}")
        return {"fields": []}

@app.route('/extract-fields', methods=['POST'])
def extract_form_fields():
    try:
        print("Received request")
        data = request.get_json()
        
        if not data or 'transcript' not in data:
            print("Invalid input format")
            return jsonify({'error': 'Invalid input format'}), 400
        
        print(f"Processing transcript: {data['transcript']}")
        result = extract_fields_with_gemini(data['transcript'])
        
        print(f"Returning result: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting server...")
    app.run(debug=True, port=8000)
