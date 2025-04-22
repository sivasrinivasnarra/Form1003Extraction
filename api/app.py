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

# Form 1003 specific fields and their patterns
FORM_1003_FIELDS = {
    "Borrower Name": {
        'patterns': [
            r"borrower(?:'s)?\s+name\s+is\b",
            r"speaking\s+with\b",
            r"\b(?:mr|mrs|ms|dr)\.\s+",
            r"(?:I am|I'm|this is)\s+",
        ],
        'format': r'^[A-Za-z\s\.-]+$',
        'section': 'Section I: Borrower Information'
    },
    "Loan Amount": {
        'patterns': [
            r"loan\s+(?:amount|of|for)\s+",
            r"requesting\s+(?:a\s+)?(?:loan\s+)?(?:of\s+)?\$?",
            r"borrow(?:ing)?\s+",
            r"mortgage\s+(?:of|for)\s+",
        ],
        'format': r'^\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?$',
        'section': 'Section L: Loan and Property Information'
    },
    "Property Address": {
        'patterns': [
            r"(?:property|address|located)\s+(?:at|is)\s+",
            r"looking\s+at\s+",
            r"buying\s+(?:at|in)\s+",
        ],
        'format': r'^\d+\s+[A-Za-z0-9\s,\.]+$',
        'section': 'Section L: Loan and Property Information'
    },
    "Annual Income": {
        'patterns': [
            r"(?:annual|yearly|base)\s+income\s+(?:is|of)\s+",
            r"makes\s+",
            r"earning\s+",
            r"salary\s+(?:is|of)\s+",
        ],
        'format': r'^\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?$',
        'section': 'Section 1a: Employment Information'
    },
    "Employment Info": {
        'patterns': [
            r"(?:work(?:s|ing)?|employed)\s+(?:at|with|for)\s+",
            r"(?:job|position|role)\s+(?:is|as)\s+",
        ],
        'format': r'^.+$',
        'section': 'Section 1a: Employment Information'
    },
    "Property Type": {
        'patterns': [
            r"(?:property|home)\s+(?:is|type)\s+(?:a)?\s+",
            r"(?:buying|looking at)\s+(?:a)?\s+",
        ],
        'format': r'^[A-Za-z\s\-]+$',
        'section': 'Section L: Loan and Property Information'
    },
    "Loan Purpose": {
        'patterns': [
            r"(?:looking to|want to|planning to)\s+",
            r"(?:refinance|purchase|buying)\b",
        ],
        'format': r'^(?:Purchase|Refinance)$',
        'section': 'Section L: Loan and Property Information'
    }
}

def calculate_confidence(field_name, value, transcript):
    """Calculate confidence score based on Form 1003 specific patterns and context"""
    confidence = 0.5  # Base confidence
    
    field_info = FORM_1003_FIELDS.get(field_name, {})
    
    # Check for pattern matches
    for pattern in field_info.get('patterns', []):
        if re.search(pattern, transcript, re.IGNORECASE):
            confidence += 0.2
            break
    
    # Check value format
    if field_info.get('format') and re.match(field_info['format'], value.strip()):
        confidence += 0.15
    
    # Context analysis
    context_window = 50
    value_pos = transcript.find(value)
    if value_pos != -1:
        context = transcript[max(0, value_pos - context_window):
                           min(len(transcript), value_pos + len(value) + context_window)]
        if any(re.search(pattern, context, re.IGNORECASE) for pattern in field_info.get('patterns', [])):
            confidence += 0.15
    
    # Field-specific adjustments
    if field_name == "Borrower Name":
        name_parts = value.split()
        if len(name_parts) >= 2:  # Full name is more likely correct
            confidence += 0.1
    elif field_name == "Loan Amount":
        if re.match(r'^\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?$', value):
            confidence += 0.1
    elif field_name == "Property Type":
        valid_types = ['Single Family', 'Condo', 'Townhouse', 'Multi-Family', 'Manufactured']
        if any(t.lower() in value.lower() for t in valid_types):
            confidence += 0.1
    
    return round(min(max(confidence, 0.0), 1.0), 2)

def extract_fields_with_gemini(transcript):
    try:
        # Form 1003 specific prompt with comprehensive examples
        prompt = f"""You are a mortgage loan processor expert. Extract information from the transcript that matches fields from the Uniform Residential Loan Application (Form 1003).

# POSITIVE EXAMPLES (Clear, straightforward cases)

Example 1 (Standard Case):
Transcript: "Hi, I'm John Smith. I'm looking to get a $300,000 mortgage for 123 Main St, Boston. I make $85,000 a year working as a software engineer at Tech Corp."
Output:
Borrower Name: John Smith
Loan Amount: $300,000
Property Address: 123 Main St, Boston
Annual Income: $85,000
Employment Info: Software Engineer at Tech Corp
Property Type: Not specified
Loan Purpose: Purchase

Example 2 (Refinance Case):
Transcript: "I'd like to refinance my condo at 456 Park Ave, NYC. My name is Sarah Johnson, I earn $120,000 annually as a marketing director."
Output:
Borrower Name: Sarah Johnson
Loan Amount: Not specified
Property Address: 456 Park Ave, NYC
Annual Income: $120,000
Employment Info: Marketing Director
Property Type: Condo
Loan Purpose: Refinance

Example 3 (Complete Information):
Transcript: "Hello, Dr. Maria Garcia-Rodriguez here. I want to purchase a single-family home at 789 Oak Drive, Austin, TX. The loan amount would be $450,000, and I'm currently making $175,000 per year as a senior physician at Central Hospital."
Output:
Borrower Name: Dr. Maria Garcia-Rodriguez
Loan Amount: $450,000
Property Address: 789 Oak Drive, Austin, TX
Annual Income: $175,000
Employment Info: Senior Physician at Central Hospital
Property Type: Single-family
Loan Purpose: Purchase

# COMPLEX EXAMPLES (Multiple or indirect mentions)

Example 4 (Multiple Amounts):
Transcript: "I'm Robert Chen, earning about $95,000 base salary plus $30,000 bonus. Looking at a $425,000 loan for a townhouse at 321 Pine Street, Seattle."
Output:
Borrower Name: Robert Chen
Loan Amount: $425,000
Property Address: 321 Pine Street, Seattle
Annual Income: $125,000
Employment Info: Not specified
Property Type: Townhouse
Loan Purpose: Not specified

Example 5 (Indirect References):
Transcript: "The property we discussed last time, you know, that manufactured home on 567 Lake Road, Miami? I'm ready to move forward. As discussed, my yearly take-home is one-fifty thousand, and we'll need financing for three-twenty-five thousand."
Output:
Borrower Name: Not specified
Loan Amount: $325,000
Property Address: 567 Lake Road, Miami
Annual Income: $150,000
Employment Info: Not specified
Property Type: Manufactured
Loan Purpose: Not specified

# EDGE CASES (Unusual formats or partial information)

Example 6 (Hyphenated/Special Characters):
Transcript: "Jean-Pierre O'Connor speaking. Looking at 42-B West 73rd St., Apt. 5C, New York, NY. Currently at Deutsche-Bank making $225K/year."
Output:
Borrower Name: Jean-Pierre O'Connor
Loan Amount: Not specified
Property Address: 42-B West 73rd St., Apt. 5C, New York, NY
Annual Income: $225,000
Employment Info: Deutsche-Bank
Property Type: Not specified
Loan Purpose: Not specified

Example 7 (Informal Language):
Transcript: "Hey there! Name's Mike - Michael Thompson officially. Making around 6 figures - about 100k actually, working remote for Apple. Wanna buy this sweet multi-family unit at 888 Beach Blvd."
Output:
Borrower Name: Michael Thompson
Loan Amount: Not specified
Property Address: 888 Beach Blvd
Annual Income: $100,000
Employment Info: Apple
Property Type: Multi-family
Loan Purpose: Purchase

Example 8 (Minimal Information):
Transcript: "James Wilson. Need 275k for the condo."
Output:
Borrower Name: James Wilson
Loan Amount: $275,000
Property Address: Not specified
Annual Income: Not specified
Employment Info: Not specified
Property Type: Condo
Loan Purpose: Not specified

# NEGATIVE EXAMPLES (Invalid or unclear cases)

Example 9 (Ambiguous Information):
Transcript: "Someone mentioned a property on Oak Street, might be interested in that or the one on Pine Avenue. Income varies, sometimes 80k, sometimes more."
Output:
Borrower Name: Not specified
Loan Amount: Not specified
Property Address: Not specified
Annual Income: Not specified
Employment Info: Not specified
Property Type: Not specified
Loan Purpose: Not specified

Example 10 (Conflicting Information):
Transcript: "John Smith - no wait, it's James Smith. The loan would be 400k - actually, make that 450k. Located at 123 Main St - sorry, 321 Main St."
Output:
Borrower Name: Not specified
Loan Amount: Not specified
Property Address: Not specified
Annual Income: Not specified
Employment Info: Not specified
Property Type: Not specified
Loan Purpose: Not specified

Now extract information from this transcript, following Form 1003 sections:
{transcript}

Format each field exactly as:
Field: Value
Use 'Not specified' if:
1. The field is not mentioned in the transcript
2. The information is ambiguous or conflicting
3. The format doesn't match expected patterns

Remember:
- Extract only clearly stated information
- Maintain original formatting for numbers and addresses
- Do not interpret or assume information not explicitly stated
- For conflicting information, mark as 'Not specified'
"""

        print("Sending Form 1003 specific prompt to Gemini...")
        response = model.generate_content(prompt)
        print(f"Received response: {response.text}")

        # Process the response and calculate confidence scores
        fields = []
        for line in response.text.split('\n'):
            line = line.strip()
            if ':' in line:
                try:
                    field_name, value = [x.strip() for x in line.split(':', 1)]
                    
                    # Only include fields with actual values
                    if value and value.lower() != 'not specified':
                        confidence = calculate_confidence(field_name, value, transcript)
                        fields.append({
                            "field_name": field_name,
                            "field_value": value,
                            "confidence_score": confidence
                        })
                except Exception as e:
                    print(f"Error processing line '{line}': {str(e)}")

        print(f"Processed Form 1003 fields with confidence scores: {fields}")
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
