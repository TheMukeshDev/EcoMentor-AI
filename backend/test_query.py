import os
from dotenv import load_dotenv
from app import create_app
from app.repositories.carbon_history_repository import CarbonHistoryRepository

load_dotenv()
app = create_app()

with app.app_context():
    db = app.extensions.get("firestore")
    repo = CarbonHistoryRepository(db)
    try:
        results = repo.find_by_user_and_date_range("XFdjXEXbNpXiRuTK7ORRaNRitIs1", "2026-06-01", "2026-06-18")
        print("Success:", results)
    except Exception as e:
        print("Error:", e)
