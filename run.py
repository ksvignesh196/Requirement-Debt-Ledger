"""
Requirement Debt Ledger (RDL) - Application Launcher
Run this script to start the server: python run.py
"""
import sys
import uvicorn
from app.database import init_db

if __name__ == "__main__":
    init_db()
    print("Requirement Debt Ledger is running at http://127.0.0.1:8000")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
