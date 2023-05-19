from ..dto.session import SessionData
from fastapi import HTTPException, Depends
from fastapi import Depends
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from uuid import UUID, uuid4


class BasicVerifier(SessionVerifier[UUID, SessionData]):
    def __init__(
            self,
            *,
            identifier: str,
            auto_error: bool,
            backend: InMemoryBackend[UUID, SessionData],
            auth_http_exception: HTTPException,
    ):
        self._identifier = identifier
        self._auto_error = auto_error
        self._backend = backend
        self._auth_http_exception = auth_http_exception

    @property
    def identifier(self):
        return self._identifier

    @property
    def backend(self):
        return self._backend

    @property
    def auto_error(self):
        return self._auto_error

    @property
    def auth_http_exception(self):
        return self._auth_http_exception

    def verify_session(self, model: SessionData) -> bool:
        """If the session exists, it is valid"""
        return True


cookie_params = CookieParameters()

# Uses UUID
cookie = SessionCookie(
    cookie_name="cookie",
    identifier="general_verifier",
    auto_error=True,
    secret_key="DONOTUSE",
    cookie_params=cookie_params,
)

backend = InMemoryBackend[UUID, SessionData]()

verifier = BasicVerifier(
    identifier="general_verifier",
    auto_error=True,
    backend=backend,
    auth_http_exception=HTTPException(status_code=403, detail="invalid session"),
)


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





