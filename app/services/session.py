from ..dto.session import SessionData, SessionCookie, SessionVerifier, CookieParameters, cookie, verifier, backend
from fastapi import Depends
from uuid import uuid4, UUID

class SessionService:
    def __init__(self, session_data: SessionData = None, session_id: UUID = None):
        self.session_data = None
        self.session_id = None
        self.job_id = None

    async def create_session(self, user, response):
        self.session_id = uuid4()
        remote_loc = f"/home/{user}/{hash(self.session_id)}/"
        remote_loc_pet = f"/home/{user}/{hash(self.session_id)}/pet/"
        cluster_name = "cluster.dieterichlab.org"
        log_file = f"{hash(self.session_id)}/logging.txt"
        last_pos_file = f"{hash(self.session_id)}/last_pos.txt"
        self.session_data = SessionData(username=user, remote_loc=remote_loc, remote_loc_pet=remote_loc_pet,
                                        cluster_name=cluster_name, log_file=log_file, last_pos_file=last_pos_file)
        self.create_cookie(response=response)
        await self.create_backend()
        return self

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

    def set_job_id(self, job_id):
        self.job_id = job_id

    def get_job_id(self):
        return self.job_id
