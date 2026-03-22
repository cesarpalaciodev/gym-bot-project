# ==================================================
# CONFIGURACION
# ==================================================

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MONGO_URI = os.getenv("MONGO_URI", "")

DATA_DIR = "data"
BACKUP_DIR = "backup"
REPORTS_DIR = "reports"
LOGS_DIR = "logs"

EXCEL_FILE = f"{REPORTS_DIR}/reporte_gimnasio.xlsx"
BACKUP_FOLDER = BACKUP_DIR

GRACE_DAYS = 4
LATE_DAYS = 5

PLANS = {
    "1": {"name": "Mensual", "months": 1, "price": 70000},
}

ADMIN_ROLES = {
    "super_admin": ["all"],
    "admin": ["members", "payments", "reports", "stats", "export"],
    "viewer": ["reports", "stats"],
}
