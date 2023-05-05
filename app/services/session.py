from ..dto.session import SessionData, SessionCookie, SessionVerifier, CookieParameters, cookie, verifier, backend
from fastapi import Depends
from uuid import uuid4, UUID

class SessionService:
    def __init__(self, session_data: SessionData = Depends(verifier), session_id: UUID = Depends(cookie)):
        self.session_data = session_data
        self.session_id = session_id

    async def create_backend(self):
        return await backend.create(self.session_id, self.session_data)

    def create_cookie(self, response=None):
        return cookie.attach_to_response(response, self.session_id)

    def get_session(self):
        return self.session_id, self.session_data

    def get_session_id(self):
        return self.session_id

    def get_session_data(self):
        return self.session_data
