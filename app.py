import os
import io
import docx
import uuid  # Added this import
from openai import OpenAI
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from typing import Optional
import streamlit as st

# Load environment variables from a specific .env file (test.env)
load_dotenv(dotenv_path='.env')

# Initialize the OpenAI client with the API key from the loaded .env file
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Optionally, print to check if the key is loaded correctly
# if openai.api_key:
#     print("API key loaded successfully.")
# else:
#     print("Error: OPENAI_API_KEY not set.")

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
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                # "content": f"Read the following document and extract a list of assignments, tests, midterms, and final exams, including the name, due date, and weight (if available). Display a check list in chronological order based on due dates. Here is the document text:\n\n{text}"
                "content": f"""The following document is a course syllabus. Your task is to extract and display the following information in the exact format provided:
                
                # Methods of Evaluation
                A breakdown of the methods of evaluation. This will likely be grouped in one section of the syllabus, and could include due dates and percentages. In a table, include the name of the evaluation method, the percent weight of the final course grade, and a date if applicable. 
                Use the exact names of the methods of evaluation provided, do not change anything from the document. Here is the format of the table:
                
                    Name | % of course grade | Date if applicable

                # Weekly Schedule
                Formatted in a table, a week-by-week schedule of all required items for the course. This includes any tasks that are due, and any lectures, labs, or tutorials that must be attended in the week. If a particular type of activity (eg. lab) does not apply to the course, omit its column from the table. Here is an example week by week schedule table:
                    Week 1 | This week's course material | Labs to attend | Quizzes or assignments due
                    Week 2 | This week's course material | Labs to attend | Quizzes or assignments due
                    Week 3 | This week's course material | Labs to attend | Quizzes or assignments due
                    etc.

                Here is the document text:
                {text}"""
            }],
            max_tokens=1000
        )

        assignments_text = response.choices[0].message.content.strip()
        return assignments_text

    except Exception as e:
        st.error(f"Error with OpenAI API: {str(e)}")
        return None

def initialize_session_state():
    if 'courses' not in st.session_state:
        st.session_state.courses = {}  # Dict to store course data

def extract_course_name(analysis_text: str) -> str:
    # Placeholder - modify based on your needs
    try:
        return "New Course"  # Default name until analysis is complete
    except:
        return "New Course"

def create_dropdown_menu(course_id):
    # Create the dropdown menu using columns for layout
    menu_container = st.container()
    with menu_container:
        col1, col2 = st.columns([6, 1])
        with col2:
            # Use a custom class for the expander
            with st.expander("⋮", expanded=False):
                st.button("🔄 Replace Syllabus", 
                         key=f"replace_{course_id}",
                         on_click=lambda: handle_replace(course_id),
                         use_container_width=True)
                
                st.button("🗑️ Remove Course", 
                         key=f"remove_{course_id}",
                         on_click=lambda: handle_remove(course_id),
                         use_container_width=True)

def handle_replace(course_id):
    st.session_state.courses[course_id] = {
        'name': 'New Course',
        'syllabus_text': None,
        'analysis': None,
        'file_uploaded': False
    }
    st.rerun()

def handle_remove(course_id):
    del st.session_state.courses[course_id]
    st.rerun()

# Add custom CSS for styling
st.markdown("""
    <style>
    /* Style for dropdown menu container */
    .stExpander {
        position: relative;
        min-width: 200px !important;
        margin-right: -150px !important;
    }

    /* Make the expander content overlay other content */
    .streamlit-expanderContent {
        position: absolute !important;
        z-index: 999 !important;
        background-color: white !important;
        border: 1px solid #ddd !important;
        border-radius: 4px !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
        width: 200px !important;
        right: 0 !important;
    }

    /* Style for menu buttons */
    .stExpander .stButton button {
        background-color: transparent;
        border: none;
        width: 100%;
        text-align: left;
        padding: 8px 16px;
        line-height: 1.5;
        white-space: nowrap;
    }

    .stExpander .stButton button:hover {
        background-color: #f0f2f6;
    }

    /* Style for expander header */
    .streamlit-expanderHeader {
        border: none;
        background-color: transparent;
        justify-content: flex-end;
        padding-right: 1rem;
    }

    /* Hide default expander styling */
    .streamlit-expanderHeader div {
        display: none;
    }

    /* Show only the trigger icon */
    .streamlit-expanderHeader div:last-child {
        display: block;
    }
    </style>
""", unsafe_allow_html=True)

def extract_course_name(analysis_text: str) -> str:
    """Extract course code/name from the syllabus analysis."""
    try:
        # Split text into lines
        lines = analysis_text.split('\n')
        
        # Look for course code/name in the first few lines
        for line in lines[:10]:  # Check first 10 lines
            # Common patterns for course codes
            if any(pattern in line.upper() for pattern in ['CS ', 'COMPSCI', 'COMPUTER SCIENCE']):
                # Extract the course code using common patterns
                if 'CS ' in line:
                    return line[line.find('CS '):].split()[0:2]  # Get "CS XXXX"
                elif 'COMPSCI' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'COMPSCI' in part.upper():
                            return f"CS {parts[i+1]}" if i+1 < len(parts) else part
        
        # If no specific course code found, look for any course identifier
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                if any(word in key.upper() for word in ['COURSE', 'CLASS']):
                    return value.strip()
        
        return "New Course"  # Default if no course name found
    except:
        return "New Course"

def course_tab(course_id):
    course_data = st.session_state.courses[course_id]
    
    # Header section with course name and dropdown menu
    col1, col2 = st.columns([6, 1])
    with col1:
        if course_data.get('file_uploaded'):
            st.header(course_data['name'])
    with col2:
        if course_data.get('file_uploaded'):
            create_dropdown_menu(course_id)

    # Upload section
    if not course_data.get('file_uploaded'):
        uploaded_file = st.file_uploader(
            "Upload course syllabus",
            type=['pdf', 'docx'],
            key=f"file_{course_id}"
        )

        if uploaded_file is not None:
            with st.spinner('Processing syllabus...'):
                try:
                    if uploaded_file.type == "application/pdf":
                        text = read_pdf(uploaded_file)
                    else:
                        text = read_docx(uploaded_file)
                    
                    analysis = analyze_with_openai(text)
                    if analysis:
                        course_name = extract_course_name(analysis)
                        course_data['syllabus_text'] = text
                        course_data['analysis'] = analysis
                        course_data['name'] = course_name
                        course_data['file_uploaded'] = True
                        st.success("Syllabus processed successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error processing document: {str(e)}")
    else:
        # Display analysis if syllabus exists
        if course_data['analysis']:
            st.markdown(course_data['analysis'])

# Add custom CSS for styling
st.markdown("""
    <style>
    /* Style for dropdown menu */
    .stButton button {
        background-color: transparent;
        border: none;
        width: 100%;
        text-align: left;
        padding: 0.25rem 0.5rem;
    }
    .stButton button:hover {
        background-color: #f0f2f6;
    }
    
    /* Style for expander */
    .streamlit-expanderHeader {
        border: none;
        background-color: transparent;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    st.title("📚 Course Syllabus Manager")
    
    # Initialize session state
    initialize_session_state()

    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        st.error("Please set your OPENAI_API_KEY environment variable")
        st.stop()

    # Add course button
    if st.button("+ Add Course"):
        new_course_id = str(uuid.uuid4())
        st.session_state.courses[new_course_id] = {
            'name': 'New Course',
            'syllabus_text': None,
            'analysis': None,
            'file_uploaded': False
        }
        st.rerun()

    # Display courses as tabs
    if st.session_state.courses:
        # Get course names for tabs
        courses = {cid: data['name'] for cid, data in st.session_state.courses.items()}
        tabs = st.tabs(list(courses.values()))
        
        # Display each course's content in its tab
        for (course_id, course_name), tab in zip(courses.items(), tabs):
            with tab:
                course_tab(course_id)
    else:
        st.info("Add a course to get started!")

if __name__ == "__main__":
    main()