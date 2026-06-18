from google.cloud import firestore
from google.oauth2 import service_account

db = None


def init_firestore(app):
    global db

    project = app.config["GCP_PROJECT_ID"]
    emulator = app.config.get("FIRESTORE_EMULATOR_HOST")

    if emulator:
        db = firestore.Client(
            project=project,
            client_options={"api_endpoint": f"http://{emulator}"},
        )
    else:
        private_key = app.config.get("FIREBASE_PRIVATE_KEY")
        client_email = app.config.get("FIREBASE_CLIENT_EMAIL")

        if private_key and client_email:
            # Format the private key newlines correctly
            formatted_key = private_key.replace("\\n", "\n")
            info = {
                "type": "service_account",
                "project_id": project,
                "private_key": formatted_key,
                "client_email": client_email,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            credentials = service_account.Credentials.from_service_account_info(info)
            db = firestore.Client(project=project, credentials=credentials)
        else:
            db = firestore.Client(project=project)

    app.extensions["firestore"] = db
