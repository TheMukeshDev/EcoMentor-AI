class DashboardService:
    def __init__(self, footprint_repository, activity_repository):
        self._footprint_repo = footprint_repository
        self._activity_repo = activity_repository

    def get_summary(self, user_id):
        pass

    def get_history(self, user_id, period):
        pass

    def get_stats(self, user_id):
        pass
