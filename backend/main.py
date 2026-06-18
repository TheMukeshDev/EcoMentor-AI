import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app

config_name = os.getenv("APP_ENV", "development")
app = create_app(config_name)


@app.route("/health")
def health():
    return {"status": "healthy"}
