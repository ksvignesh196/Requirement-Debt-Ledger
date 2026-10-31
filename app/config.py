"""
Requirement Debt Ledger (RDL) - Application Configuration
"""
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "rdl.db"

# Security & CORS configuration
# Restricted to explicitly configured trusted origins. Can be extended via RDL_ALLOWED_ORIGINS env var.
DEFAULT_ALLOWED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]
env_origins = os.getenv("RDL_ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = [o.strip() for o in env_origins.split(",") if o.strip()] or DEFAULT_ALLOWED_ORIGINS

# Risk Engine Parameters
DEFAULT_WEIGHT_BUSINESS = 0.35
DEFAULT_WEIGHT_ARCHITECTURE = 0.35
DEFAULT_WEIGHT_SAFETY = 0.30

# Time-dependent interest parameters
DEFAULT_GRACE_PERIOD_DAYS = 14
DEFAULT_DAILY_INTEREST_RATE = 0.008  # 0.8% compound increase per day past grace

# Overdue penalty parameters:
# Penalty grows at 25% per 30-day epoch overdue, capped at a maximum 2.0x multiplier (+100% surcharge).
OVERDUE_PENALTY_RATE_PER_MONTH = 0.25
MAX_OVERDUE_PENALTY_MULTIPLIER = 2.0

# Priority Weights (Debt Priority Index - DPI)
WEIGHT_RISK = 0.45
WEIGHT_DOWNSTREAM = 0.25
WEIGHT_URGENCY = 0.20
WEIGHT_COST_OF_DELAY = 0.10

# Effort-Aware Recommendation Weights (Analytic Hierarchy Process / MCDM)
REC_WEIGHT_DYNAMIC_RISK = 0.35
REC_WEIGHT_CASCADED_UNBLOCK = 0.30
REC_WEIGHT_BUSINESS_VALUE = 0.20
REC_WEIGHT_URGENCY = 0.15
REC_EFFORT_ELASTICITY = 0.70  # Sub-linear effort penalty factor

# Escalation thresholds (days)
ESCALATION_WARNING_DAYS = 7  # Warn within 7 days of review date

# Release Gate Defaults
DEFAULT_MAX_CRITICAL_DEBTS = 0
DEFAULT_MAX_HIGH_DEBTS = 1
DEFAULT_MAX_AGGREGATE_RISK = 150.0

# Audit Hash Chain Genesis Seed
AUDIT_GENESIS_PREV_HASH = "0000000000000000000000000000000000000000000000000000000000000000"
