# backend/langchain_logic.py
from pinecone import Pinecone
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import time
load_dotenv(override=True)
import os
import re
import requests

print("DEBUG GOOGLE_API_KEY:", os.getenv("GOOGLE_API_KEY"))
pc=Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name="automated-performance-evaluator-logs"
index = pc.Index(index_name)

def split_employee_logs(logs: str):
    """
    Splits logs into chunks where each chunk corresponds
    to a single employee entry.
    """
    # Regex to match "Employee E001 ..." until the next "Employee"
    pattern = r"(Employee\s+E\d+\s.*?)(?=(?:\nEmployee\s+E\d+)|\Z)"
    
    matches = re.findall(pattern, logs, flags=re.DOTALL)
    
    # Clean up chunks
    chunks = [m.strip() for m in matches if m.strip()]
    return chunks

def store_logs(employee_id: str, logs: str):
    """Store logs in Pinecone using MaaS (llama-text-embed-v2)."""
    # splitter = RecursiveCharacterTextSplitter(chunk_size=250, chunk_overlap=100)
    chunks = split_employee_logs(logs)
    print(chunks)
    records = []
    for i, chunk in enumerate(chunks):
        records.append({
            "id": f"{employee_id}-{i}",  # ✅ Must be "id", since Pinecone will use this as the document ID
            "text": chunk  # ✅ Must be "text", since Pinecone will embed this
            
        })
    
    if records:
        namespace = f"employee-{employee_id}"
        index.upsert_records(namespace=namespace, records=records)
        

def retrieve_logs(employee_id: str, query: str, top_k: int = 3) -> str:
    """Retrieve most relevant logs using Pinecone MaaS query."""
    results = index.search(
        namespace=f"employee-{employee_id}",
        query={
            "inputs": {"text": query},
            "top_k": top_k,
        }
    )
    print("Result is:", results)
    hits = results.get("result", {}).get("hits", [])
    if not hits:
        return "No logs found for this employee."

    # ✅ return first hit’s text
    return hits[0]["fields"]["text"]


# -----------------------------
# Prompt Template
# -----------------------------
template = """
You are an HR performance evaluator.
Given the following employee logs, evaluate the performance of the employee {employee_id}.

Criteria:
1. Productivity – tasks completed
2. Efficiency – balance of activities
3. Quality – fewer bugs/errors

Return a structured report with:
- Employee ID
- Summary
- Strengths
- Weaknesses
- Performance Rating (Excellent, Good, Needs Improvement)
- Suggestions
Kindly maintain the structure and formatting as specified.

Logs:
{context}
"""


prompt = PromptTemplate(template=template, input_variables=["employee_id", "context"])

# -----------------------------
# LLM (Google Generative AI)
# -----------------------------
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash",google_api_key=os.getenv("GOOGLE_API_KEY"),temperature=0)

# -----------------------------
# Main pipeline function
# -----------------------------
def evaluate_employee(employee_id: str, logs: str) -> str:
    """Generate performance evaluation for a given employee from logs."""

    store_logs(employee_id, logs)
    print("store_logs ran successfully.")
    time.sleep(20)  # Wait for a moment to ensure data is stored
    print("Fetching logs now...")
    query = f"Give all logs for employee {employee_id}"
    context_text = retrieve_logs(employee_id, query)
    print("context_text fetched:", context_text)

    # 4. Format final prompt
    final_prompt = prompt.invoke({"employee_id": employee_id, "context": context_text})

    # 5. Run LLM
    answer = llm.invoke(final_prompt)

    return answer.content


def clean_summary(text: str) -> str:
    # Remove multiple blank lines
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    # Strip leading/trailing whitespace
    return text.strip()