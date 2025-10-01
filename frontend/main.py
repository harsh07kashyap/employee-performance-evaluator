import streamlit as st
import requests
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import time
import os


API_URL = os.getenv("API_URL", "http://localhost:8000")
api_endpoint_for_summary_generation = f"{API_URL}/generate_report"

st.set_page_config(page_title="AI Performance Insights", page_icon="💡", layout="wide")

# ---------- Custom CSS ----------
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stApp > header { background-color: #f0f2f6; }
    .main-header {
        text-align: left; color: #333333; font-weight: 600;
        padding-top: 10px; padding-bottom: 5px;
        border-bottom: 2px solid #e0e0e0; margin-bottom: 20px;
    }
    div.stButton > button {
        background-color: #f7931e; color: white;
        border-radius: 8px; border: none;
        padding: 10px 20px; font-weight: bold;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover { background-color: #e5820d; }
    .report-box {
        background: #ffffff; border: 1px solid #e0e0e0;
        padding: 20px; border-radius: 12px;
        font-size: 15px; line-height: 1.6;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.08);
        min-height: 350px; white-space: pre-wrap;
    }
    .stTextArea textarea, .stTextInput input, .stSelectbox > div {
        border-radius: 8px; border: 1px solid #dcdcdc;
        padding: 10px; font-size: 14px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- PDF Generation ----------
def create_pdf(summary_text: str, employee_id: str) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 40, f"Performance Evaluation for Employee: {employee_id}")
    c.line(50, height - 50, width - 50, height - 50)
    c.setFont("Helvetica", 12)

    y = height - 80
    for line in summary_text.split("\n"):
        c.drawString(50, y, line)
        y -= 18
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 12)
    c.save()
    buffer.seek(0)
    return buffer.read()


# ---------- Header ----------
st.markdown("## 💡 AI Performance Insights", unsafe_allow_html=True)
st.markdown("<div class='main-header'>Automated Employee Performance Evaluator</div>", unsafe_allow_html=True)


# ---------- Layout ----------
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("Generate Evaluation")

    # --- Sample Logs Buttons ---
    col_btn1, col_btn2 = st.columns(2)
    default_logs = ""

    sample_logs_1 = """Employee E001 is a Data Scientist. 
On 11th September, they completed 11 tasks, made 5 commits, fixed 2 bugs, implemented 2 features, 
created 4 reports, attended 1 meeting, and worked actively for 6.1 hours. 
Manager’s review: Excellent. They also ran 2 experiments.

Employee E002 is a Software Engineer.
On 11th September, they completed 9 tasks, made 12 commits, fixed 5 bugs, implemented 3 features, reviewed 2 pull requests, attended 2 meetings, and worked actively for 7.4 hours.
Manager’s review: Very Good. They also refactored 1 module.

Employee E003 is a Business Analyst.
On 11th September, they completed 7 tasks, prepared 3 reports, conducted 2 requirement sessions, analyzed 1 dataset, attended 3 meetings, and worked actively for 6.0 hours.
Manager’s review: Good. They also created 1 presentation deck.

Employee E004 is a DevOps Engineer.
On 11th September, they completed 8 tasks, deployed 2 releases, fixed 3 CI/CD issues, wrote 4 infrastructure scripts, monitored 2 incidents, attended 1 meeting, and worked actively for 7.2 hours.
Manager’s review: Excellent. They also automated 1 backup routine.

Employee E005 is a QA Engineer.
On 11th September, they completed 10 tasks, executed 35 test cases, logged 6 bugs, verified 3 bug fixes, wrote 2 automation scripts, attended 1 meeting, and worked actively for 6.5 hours.
Manager’s review: Very Good. They also prepared 1 test plan."""

    sample_logs_2 = """Employee E006 is a UI/UX Designer.
On 12th September, they completed 6 tasks, created 3 wireframes, designed 2 prototypes, reviewed 1 design audit, collaborated on 2 feedback sessions, attended 2 meetings, and worked actively for 6.8 hours.
Manager’s review: Excellent. They also updated 1 design guideline document.

Employee E007 is a Data Scientist.
On 13th September, they completed 10 tasks, made 4 commits, built 1 machine learning model, fixed 2 data pipeline issues, prepared 2 reports, attended 1 meeting, and worked actively for 7.0 hours.
Manager’s review: Very Good. They also ran 3 experiments.

Employee E008 is a Software Engineer.
On 12th September, they completed 12 tasks, made 15 commits, fixed 4 bugs, implemented 2 features, reviewed 1 pull request, attended 2 meetings, and worked actively for 7.6 hours.
Manager’s review: Excellent. They also optimized 1 database query.

Employee E009 is a DevOps Engineer.
On 14th September, they completed 9 tasks, deployed 1 release, fixed 2 monitoring alerts, wrote 3 automation scripts, updated 1 server configuration, attended 2 meetings, and worked actively for 6.9 hours. Manager’s review: Good. They also tested 1 disaster recovery drill.

Employee E010 is a QA Engineer.
On 13th September, they completed 11 tasks, executed 42 test cases, logged 7 bugs, verified 4 bug fixes, created 2 regression test suites, attended 1 meeting, and worked actively for 6.3 hours.
Manager’s review: Very Good. They also updated 1 automation framework."""

    logs_input = ""

    with col_btn1:
        if st.button("Insert Sample Logs 1"):
            default_logs = sample_logs_1

    with col_btn2:
        if st.button("Insert Sample Logs 2"):
            default_logs= sample_logs_2

    # Text Area (if no button pressed, it stays empty)
    logs_input = st.text_area(
        "Enter your company's employee performance logs or relevant data:",
        value=default_logs if default_logs else st.session_state.get("_logs_backup", ""),
        height=180,
        placeholder="e.g., Provide a balanced performance review..."
    )
    
     # Save current input as backup to survive re-runs
    st.session_state["_logs_backup"] = logs_input

    # Dropdown
    employees = ["E001", "E002", "E003", "E004","E005", "E006", "E007", "E008", "E009", "E010"]
    employee_id = st.selectbox("Select Employee:", employees)

    st.markdown("---")

    generate_btn = st.button("Generate Summary")


with col2:
    st.subheader("Evaluation Summary")

    if generate_btn:
        if not logs_input:
            st.warning("⚠️ Please enter logs first.")
        else:
            with st.spinner(f"🔎 Analyzing logs for {employee_id}..."):
                try:
                    payload = {"employee_name": employee_id, "logs": logs_input}
                    response = requests.post(api_endpoint_for_summary_generation, json=payload, timeout=30)
                    response.raise_for_status()
                    data = response.json()
                    summary_report = data.get("report", "Error: No report returned from API.")
                except Exception as e:
                    st.error(f"❌ API error: {e}")
                    summary_report = "Summary generation failed."

            st.success(f"✅ Summary generated for {employee_id}")
            st.markdown(f"<div class='report-box'>{summary_report}</div>", unsafe_allow_html=True)

            pdf_bytes = create_pdf(summary_report, employee_id)
            st.download_button(
                label="⬇️ Download Summary as PDF",
                data=pdf_bytes,
                file_name=f"performance_summary_{employee_id}_{int(time.time())}.pdf",
                mime="application/pdf"
            )
    else:
        st.markdown("<div class='report-box'>Summary will appear here after generation.</div>", unsafe_allow_html=True)
