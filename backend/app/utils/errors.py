class AppError(Exception):
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code


class NotFoundError(AppError):
    def __init__(self, message="Resource not found"):
        super().__init__(message, status_code=404)


class ValidationError(AppError):
    def __init__(self, message="Validation failed"):
        super().__init__(message, status_code=422)


class AuthenticationError(AppError):
    def __init__(self, message="Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(AppError):
    def __init__(self, message="Permission denied"):
        super().__init__(message, status_code=403)
