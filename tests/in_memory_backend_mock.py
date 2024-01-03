from fastapi_sessions.backends.session_backend import SessionModel
from fastapi_sessions.frontends.session_frontend import ID
from fastapi_sessions.backends.implementations.in_memory_backend import InMemoryBackend


class InMemoryBackendMock(InMemoryBackend):

    def __init__(self):
        super().__init__()

    def create(self, session_id: ID, data: SessionModel):
        pass

    def update(self, session_id: ID, data: SessionModel) -> None:
        pass
