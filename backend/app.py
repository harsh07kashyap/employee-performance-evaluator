from fastapi import FastAPI
from pydantic import BaseModel
from langchain_logic import evaluate_employee
from langchain_logic import clean_summary
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Employee Performance Evaluation API")

# Allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 👈 or ["https://my-frontend.streamlit.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Pydantic Models
# -----------------------------
class LogRequest(BaseModel):
    employee_name: str
    logs: str

class ReportResponse(BaseModel):
    employee_name: str
    report: str
    

@app.post("/generate_report", response_model=ReportResponse)
def generate_report(req: LogRequest):
    """Generate employee report using LangChain pipeline"""
    raw_report = evaluate_employee(req.employee_name, req.logs)
    report = clean_summary(raw_report)
    return ReportResponse(employee_name=req.employee_name, report=report)