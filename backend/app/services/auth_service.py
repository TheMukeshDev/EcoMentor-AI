class AuthService:
    def __init__(self, user_repository):
        self._user_repo = user_repository

    def register_user(self, data):
        pass

    def authenticate_user(self, email, password):
        pass

    def get_user_profile(self, uid):
        pass

    def update_user_profile(self, uid, data):
        pass
