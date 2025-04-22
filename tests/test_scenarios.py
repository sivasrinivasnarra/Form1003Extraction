import pytest
import requests
import json
from datetime import datetime
import random

# Test data generation helpers
def generate_name():
    first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emma", "Robert", "Maria", "James", "Lisa"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def generate_address():
    street_numbers = list(range(100, 1000, 50))
    street_names = ["Oak", "Maple", "Pine", "Cedar", "Elm", "Main", "Park", "Lake", "Hill", "River"]
    street_types = ["Street", "Avenue", "Boulevard", "Road", "Lane", "Drive", "Court", "Circle", "Way", "Place"]
    cities = ["San Francisco", "Los Angeles", "New York", "Chicago", "Houston", "Miami", "Seattle", "Boston", "Denver", "Austin"]
    states = ["CA", "NY", "IL", "TX", "FL", "WA", "MA", "CO"]
    
    return f"{random.choice(street_numbers)} {random.choice(street_names)} {random.choice(street_types)}, {random.choice(cities)}, {random.choice(states)}"

def generate_loan_amount():
    base = random.randint(100, 800)
    return f"${base},000"

def generate_income():
    base = random.randint(50, 200)
    return f"${base},000"

# Test Scenarios
test_scenarios = [
    {
        "name": "Standard Positive Case",
        "transcript": lambda: f"Hi, I'm speaking with {generate_name()}. They're looking to get a mortgage for {generate_loan_amount()} for a property at {generate_address()}. Their annual income is {generate_income()}.",
        "expected_fields": ["Borrower Name", "Loan Amount", "Property Address", "Annual Income"],
        "should_pass": True
    },
    {
        "name": "Multiple Borrowers Case",
        "transcript": lambda: f"I have {generate_name()} and {generate_name()} here applying jointly for a {generate_loan_amount()} mortgage. Their combined income is {generate_income()} and they're looking at a house on {generate_address()}.",
        "expected_fields": ["Borrower Name", "Loan Amount", "Property Address", "Annual Income"],
        "should_pass": True
    },
    {
        "name": "Informal Conversation Style",
        "transcript": lambda: f"Yeah, so I was talking to {generate_name()}, really nice person. They mentioned they make about {generate_income()} a year and are hoping to get a loan for {generate_loan_amount()}. Oh, and they found this cute place at {generate_address()}.",
        "expected_fields": ["Borrower Name", "Loan Amount", "Property Address", "Annual Income"],
        "should_pass": True
    },
    {
        "name": "Missing Income Information",
        "transcript": lambda: f"The borrower {generate_name()} is interested in a {generate_loan_amount()} mortgage for the property at {generate_address()}.",
        "expected_fields": ["Borrower Name", "Loan Amount", "Property Address"],
        "should_pass": True
    },
    {
        "name": "Complex Address Format",
        "transcript": lambda: f"I'm working with {generate_name()} on a mortgage application. They're looking at Unit 4B at {generate_address()}, it's a condo. The loan amount would be {generate_loan_amount()} and they make {generate_income()} annually.",
        "expected_fields": ["Borrower Name", "Loan Amount", "Property Address", "Annual Income"],
        "should_pass": True
    },
    {
        "name": "Minimal Information",
        "transcript": lambda: f"Just {generate_name()} calling about a {generate_loan_amount()} mortgage.",
        "expected_fields": ["Borrower Name", "Loan Amount"],
        "should_pass": True
    },
    {
        "name": "Empty Transcript",
        "transcript": lambda: "",
        "expected_fields": [],
        "should_pass": False
    },
    {
        "name": "Non-English Characters",
        "transcript": lambda: f"☺ {generate_name()} wants a {generate_loan_amount()} loan for 你好 {generate_address()}.",
        "expected_fields": ["Borrower Name", "Loan Amount", "Property Address"],
        "should_pass": True
    },
    {
        "name": "Very Long Transcript",
        "transcript": lambda: f"""This is a lengthy call transcript with {generate_name()}. They started by discussing their current situation,
            mentioning their income of {generate_income()}. After some discussion about market conditions and interest rates,
            they expressed interest in a property at {generate_address()}. They're looking for a loan of {generate_loan_amount()}.
            We also discussed various other topics including property taxes, insurance requirements, and closing costs...""" * 2,
        "expected_fields": ["Borrower Name", "Loan Amount", "Property Address", "Annual Income"],
        "should_pass": True
    },
    {
        "name": "Invalid Data Format",
        "transcript": lambda: f"Name: {generate_name()}\nAmount: {generate_loan_amount()}\nAddress: {generate_address()}\nIncome: {generate_income()}",
        "expected_fields": ["Borrower Name", "Loan Amount", "Property Address", "Annual Income"],
        "should_pass": True
    }
]

def test_scenarios_with_api():
    """Run all test scenarios against the API"""
    results = []
    
    for scenario in test_scenarios:
        print(f"\nTesting Scenario: {scenario['name']}")
        
        # Generate the transcript
        transcript = scenario['transcript']()
        print("\nTranscript:")
        print(transcript)
        
        try:
            # Make API call
            response = requests.post(
                'http://localhost:8000/extract-fields',
                json={"transcript": transcript},
                headers={'Content-Type': 'application/json'}
            )
            
            # Process response
            if response.status_code == 200:
                data = response.json()
                print("\nExtracted Fields:")
                if 'fields' in data and data['fields']:
                    for field in data['fields']:
                        print(f"{field['field_name']}: {field['field_value']} (Confidence: {field['confidence_score']:.2f})")
                    
                    # Verify expected fields
                    found_fields = [field['field_name'] for field in data['fields']]
                    missing_fields = [field for field in scenario['expected_fields'] if field not in found_fields]
                    
                    if missing_fields and scenario['should_pass']:
                        print(f"\n⚠️ Warning: Missing expected fields: {missing_fields}")
                    else:
                        print("\n✅ All expected fields found")
                else:
                    print("No fields extracted")
                    if scenario['should_pass']:
                        print("\n⚠️ Warning: Expected fields but none found")
                    else:
                        print("\n✅ Expected no fields")
            else:
                print(f"\n❌ Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("\n❌ Error: Could not connect to the API. Make sure the server is running.")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
        
        print("\n" + "="*50)

if __name__ == "__main__":
    test_scenarios_with_api() 