class ActivityService:
    def __init__(self, activity_repository):
        self._activity_repo = activity_repository

    def list_activities(self, user_id):
        pass

    def log_activity(self, user_id, data):
        pass

    def get_activity(self, activity_id):
        pass

    def delete_activity(self, activity_id):
        pass
