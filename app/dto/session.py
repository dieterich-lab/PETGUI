import threading
from typing import Any
from fastapi import HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from uuid import UUID, uuid4


class SessionData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    model_config["protected_namespaces"] = ()
    username: str
    id: UUID
    remote_loc: Any = None
    remote_loc_pet: Any = None
    cluster_name: str
    last_pos_file: str
    log_file: str
    job_id: Any = None
    event: Any = None
    job_status: Any = None


cookie_params = CookieParameters()

# Uses UUID
cookie = SessionCookie(
    cookie_name="cookie",
    identifier="general_verifier",
    auto_error=True,
    secret_key="DONOTUSE",
    cookie_params=cookie_params,
)


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

backend = InMemoryBackend[UUID, SessionData]()

verifier = BasicVerifier(
    identifier="general_verifier",
    auto_error=True,
    backend=backend,
    auth_http_exception=HTTPException(status_code=403, detail="invalid session"),
)




