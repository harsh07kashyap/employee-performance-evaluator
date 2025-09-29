import streamlit as st
import requests
import json
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import time
from dotenv import load_dotenv
import os
load_dotenv(override=True)

API_URL = f"{os.getenv('API_URL', 'http://localhost:8000')}"
api_endpoint_for_summary_generation = f"{API_URL}/generate_report"

# Page config
st.set_page_config(page_title="AI Performance Insights", page_icon="💡", layout="wide")

# Custom CSS for a classy look and orange button
st.markdown("""
    <style>
    /* Main container background */
    .main {
        background-color: #f0f2f6; /* Light gray background for a clean look */
    }
    
    /* Center and style the title */
    .stApp > header {
        background-color: #f0f2f6;
    }
    .main-header {
        text-align: left;
        color: #333333;
        font-weight: 600;
        padding-top: 10px;
        padding-bottom: 5px;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 20px;
    }
    
    /* Custom styling for the generate button (Orange) */
    div.stButton > button {
        background-color: #f7931e; /* Vibrant Orange */
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover {
        background-color: #e5820d; /* Darker orange on hover */
    }
    
    /* Style for the Evaluation Summary Box (Right Column) */
    .report-box {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 20px;
        border-radius: 12px;
        font-size: 15px;
        line-height: 1.6;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.08); /* More pronounced shadow */
        min-height: 350px; /* Ensures the box has a minimum size */
        white-space: pre-wrap;
    }

    /* Input/Select box styling */
    .stTextArea textarea, .stTextInput input, .stSelectbox > div {
        border-radius: 8px;
        border: 1px solid #dcdcdc;
        padding: 10px;
        font-size: 14px;
    }
    
    </style>
""", unsafe_allow_html=True)

# Application Header (Top Bar Area)
st.markdown("## 💡 AI Performance Insights", unsafe_allow_html=True)
st.markdown("<div class='main-header'>Automated Employee Performance Evaluator</div>", unsafe_allow_html=True)


# --- PDF Generation Function ---
def create_pdf(summary_text: str, employee_id: str) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 40, f"Performance Evaluation for Employee: {employee_id}")
    c.line(50, height - 50, width - 50, height - 50)
    
    c.setFont("Helvetica", 12)
    
    # Write summary text line by line
    y = height - 80
    for line in summary_text.split("\n"):
        c.drawString(50, y, line)
        y -= 18
        if y < 50:  # New page if needed
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 12) # Reapply font for new page

    c.save()
    buffer.seek(0)
    return buffer.read()
# ------------------------------

# Initialize state for summary and employee (for persistent display)
if 'summary_report' not in st.session_state:
    st.session_state.summary_report = "Summary will appear here after generation. \n\nThe AI analyzes the provided logs and the employee's performance data, highlighting key strengths, areas for improvement, and notable achievements."
if 'employee_id' not in st.session_state:
    st.session_state.employee_id = "E001"
if 'logs_input' not in st.session_state:
    st.session_state.logs_input = ""


# --- Main Two-Column Layout ---
col1, col2 = st.columns([1, 1.2]) # Input column slightly smaller than Output column

# LEFT COLUMN: Generate Evaluation (Input)
with col1:
    st.subheader("Generate Evaluation")
    
    # Text Area for User Input/Logs (RAG Query)
    st.session_state.logs_input = st.text_area(
        "Enter your company's employee performance logs or relevant data:", 
        height=180, 
        placeholder="e.g., Provide a balanced performance review...",
        key="logs_input_area"
    )

    # Dropdown for Employee Name
    employees = ["E001", "E002", "E003", "E004","E005", "E006", "E007", "E008", "E009", "E010"]
    st.session_state.employee_id = st.selectbox(
        "Select Employee:", 
        employees, 
        key="employee_select"
    )

    st.markdown("---")
    
    # Action button
    generate_btn = st.button("Generate Summary")


# RIGHT COLUMN: Evaluation Summary (Output)
with col2:
    st.subheader("Evaluation Summary")

    # 1. Create a placeholder for the dynamic summary content
    # This placeholder will be updated inside the if generate_btn block.
    summary_placeholder = st.empty() 
    
    # 2. Display the initial content (or previous content) using the placeholder
    initial_summary_box_html = f"<div class='report-box'>{st.session_state.summary_report}</div>"
    summary_placeholder.markdown(initial_summary_box_html, unsafe_allow_html=True)
    
    # Download button placeholder (will be activated after generation)
    download_placeholder = st.empty()


# --- Logic on Button Click ---
if generate_btn:
    # Extract only the ID from the selection
    employee_id_only = st.session_state.employee_id.split(" - ")[0]
    
    if not st.session_state.logs_input or not st.session_state.employee_id:
        st.warning("⚠️ Please enter a prompt and select an employee.")
    else:
        # Clear the old download button immediately before showing spinner
        download_placeholder.empty()

        with st.spinner(f"🔎 Analyzing logs and generating summary for {employee_id_only}..."):
            try:
                # 1. API Call Logic
                payload = {"employee_name": employee_id_only, "logs": st.session_state.logs_input}
                response = requests.post(api_endpoint_for_summary_generation, json=payload, timeout=30)
                response.raise_for_status() # Raise exception for bad status codes
                data = response.json()
                
                # Check for the report key
                if 'report' in data:
                    st.session_state.summary_report = data['report']
                else:
                    st.session_state.summary_report = "Error: Report key not found in API response."
                    st.error(st.session_state.summary_report)
                    
            except requests.exceptions.ConnectionError:
                # 2. Simulated/Fallback Logic if API is unreachable (for demo/testing)
                st.error("API Connection Error: Could not connect to the backend server. Using a simulated report.")
                time.sleep(2) 
                
                # SIMULATED REPORT DATA
                st.session_state.summary_report = f"""**Employee ID: {employee_id_only}**
**Evaluation Date:** October 1, 2025

**Overall Assessment:** The employee has demonstrated strong commitment and technical expertise during this period. The RAG system analysis indicates a significant contribution to key projects.

**Key Strengths:**
* **Code Quality:** Commits show a low bug rate and good adherence to coding standards.
* **Collaboration:** Consistently provided clear and constructive feedback in code reviews.

**Areas for Development:**
* **Time Management:** Needs to improve estimation accuracy for larger tasks to prevent delays.
* **Knowledge Sharing:** Encourage more internal presentations on new technical findings.

**Recommendation:** Consider for promotion to Senior Developer within the next quarter, pending successful completion of leadership training.
"""
            except Exception as e:
                # 3. General Error
                st.error(f"❌ An unexpected error occurred: {e}")
                st.session_state.summary_report = "Summary generation failed due to an error."
                
        
        # After successful generation (or simulation), update the UI in a success block
        st.success(f"✅ Summary generated successfully for {employee_id_only}!")
        
        # 1. Update the Summary Box in the right column using the placeholder
        updated_summary_box_html = f"<div class='report-box'>{st.session_state.summary_report}</div>"
        summary_placeholder.markdown(updated_summary_box_html, unsafe_allow_html=True)

        # 2. Re-render the Download button
        pdf_bytes = create_pdf(st.session_state.summary_report, employee_id_only)
        
        with col2:
            download_placeholder.download_button(
                label="⬇️ Download Summary as PDF",
                data=pdf_bytes,
                file_name=f"performance_summary_{employee_id_only}_{int(time.time())}.pdf",
                mime="application/pdf"
            )
