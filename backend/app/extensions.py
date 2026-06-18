from google.cloud import firestore

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
        db = firestore.Client(project=project)

    app.extensions["firestore"] = db
