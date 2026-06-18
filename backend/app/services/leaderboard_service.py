class LeaderboardService:
    def __init__(self, user_repository, footprint_repository):
        self._user_repo = user_repository
        self._footprint_repo = footprint_repository

    def get_global_leaderboard(self):
        pass

    def get_friends_leaderboard(self, user_id):
        pass
