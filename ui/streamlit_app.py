import streamlit as st
import requests
import json
import pyperclip

# Configure the page
st.set_page_config(
    page_title="FormsiQ - Form Field Extractor",
    page_icon="📝",
    layout="wide"
)

# Add custom CSS
st.markdown("""
    <style>
    .stTextArea > div > div > textarea {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        font-family: monospace;
        height: 300px !important;
        min-height: 300px;
    }
    
    .stButton button {
        width: 100%;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .output-container {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        height: 300px;
        font-family: monospace;
        line-height: 1.5;
        overflow-y: auto;
        white-space: pre-wrap;
    }
    
    .title-container {
        margin-bottom: 2rem;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'transcript' not in st.session_state:
    st.session_state.transcript = ""
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = ""

def clear_fields():
    st.session_state.transcript = ""
    st.session_state.extracted_text = ""

# Title
st.markdown('<div class="title-container">', unsafe_allow_html=True)
st.title("FormsiQ - Form Field Extractor")
st.markdown('</div>', unsafe_allow_html=True)

# Create three columns
col1, col2, col3 = st.columns([5, 1, 5])

with col1:
    transcript = st.text_area(
        "Enter call transcript",
        key="transcript",
        height=300,
        placeholder="Enter the call transcript here...",
        label_visibility="collapsed"
    )

with col2:
    extract_button = st.button("🔍 Extract", use_container_width=True)

with col3:
    if extract_button and transcript:
        try:
            response = requests.post(
                'http://localhost:8000/extract-fields',
                json={"transcript": transcript},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'fields' in data and data['fields']:
                    output_lines = []
                    for field in data['fields']:
                        line = f"{field['field_name']}: {field['field_value']} (Confidence: {field['confidence_score']:.2f})"
                        output_lines.append(line)
                    st.session_state.extracted_text = "\n".join(output_lines)
                else:
                    st.session_state.extracted_text = "No fields were extracted from the transcript."
            else:
                error_message = response.json().get('error', 'Unknown error occurred')
                st.session_state.extracted_text = f"Error: {error_message}"
                
        except requests.exceptions.ConnectionError:
            st.session_state.extracted_text = "Error: Could not connect to the server. Please ensure the backend service is running."
        except Exception as e:
            st.session_state.extracted_text = f"Error: {str(e)}"
    
    st.markdown(f'<div class="output-container">{st.session_state.extracted_text}</div>', unsafe_allow_html=True)
    
    if st.session_state.extracted_text:
        if st.button("📋 Copy", use_container_width=True):
            try:
                pyperclip.copy(st.session_state.extracted_text)
                st.success("Content copied to clipboard!")
            except Exception as e:
                st.error("Failed to copy to clipboard")

# Clear button at the bottom
if st.button("🗑️ Clear", use_container_width=True, on_click=clear_fields):
    st.experimental_rerun()
