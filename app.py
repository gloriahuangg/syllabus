import os
import io
import docx
import openai
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from typing import Optional
import streamlit as st  # Import Streamlit

# Load environment variables from a specific .env file (test.env)
load_dotenv(dotenv_path='.env')

# Initialize the OpenAI client with the API key from the loaded .env file
openai.api_key = os.getenv('OPENAI_API_KEY')

# Optionally, print to check if the key is loaded correctly
if openai.api_key:
    print("API key loaded successfully.")
else:
    print("Error: OPENAI_API_KEY not set.")

def read_pdf(file) -> str:
    pdf_reader = PdfReader(io.BytesIO(file.read()))  # Wrap file in a BytesIO buffer
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def read_docx(file) -> str:
    doc = docx.Document(io.BytesIO(file.read()))  # Wrap file in a BytesIO buffer
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def analyze_with_openai(text: str) -> Optional[str]:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Or another model of your choice
            messages=[{
                "role": "user",
                "content": f"Read the following document and extract a list of assignments, tests, midterms, and final exams, including the name, due date, and weight (if available). Display a check list in chronological order based on due dates. Here is the document text:\n\n{text}"
            }],
            max_tokens=1000  # Adjust as needed
        )

        assignments_text = response['choices'][0]['message']['content'].strip()

        return assignments_text

    except Exception as e:
        st.error(f"Error with OpenAI API: {str(e)}")
        return None

def main():
    st.title("📚 Assignment Analyzer")
    st.write("Upload a document (PDF or DOCX) and get AI-powered analysis of assignments, their due dates, and weights.")

    # Check for API key
    if not openai.api_key:
        st.error("Please set your OPENAI_API_KEY environment variable")
        st.stop()

    # File upload
    uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'docx'])

    if uploaded_file is not None:
        # Create a spinner while processing the file
        with st.spinner('Reading document...'):
            try:
                # Read the document based on its type
                if uploaded_file.type == "application/pdf":
                    text = read_pdf(uploaded_file)
                else:
                    text = read_docx(uploaded_file)

                # Store the document text in session state
                st.session_state['document_text'] = text
                st.success("Document successfully processed!")
            except Exception as e:
                st.error(f"Error processing document: {str(e)}")
                st.stop()

        # Generate analysis of assignments
        if st.button("Generate Assignment List"):
            with st.spinner('Analyzing document for assignments...'):
                analysis = analyze_with_openai(st.session_state['document_text'])
                if analysis:
                    st.markdown(analysis)
                else:
                    st.error("Failed to generate assignment list.")

if __name__ == "__main__":
    main()