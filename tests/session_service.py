from app.services.session import SessionService
from app.dto.session import cookie, backend


class SessionServiceMock(SessionService):
    """Return sample Session Service from TestServer"""
    def __init__(self, session_data, session_id):
        self.session_id = session_id
        self.session_data = session_data

    def create_session(self, user, response):
        self.create_cookie(response=response)
        self.create_backend()
        return self

    def create_backend(self):
        return backend.create(self.session_id, self.session_data)

    def create_cookie(self, response=None):
        return cookie.attach_to_response(response, self.session_id)
