from ..dto.session import SessionData, SessionCookie, SessionVerifier, CookieParameters, cookie, verifier, backend
from fastapi import Depends, Response
from uuid import uuid4, UUID

class SessionService:
    def __init__(self, session_data: SessionData = None, session_id: UUID = None):
        self.session_data = None
        self.session_id = None

    async def create_session(self, user, response: Response):
        self.session_id = uuid4()
        remote_loc = f"/home/{user}/{hash(self.session_id)}/"
        remote_loc_pet = f"/home/{user}/{hash(self.session_id)}/pet/"
        cluster_name = "cluster.dieterichlab.org"
        log_file = f"{hash(self.session_id)}/logging.txt"
        last_pos_file = f"{hash(self.session_id)}/last_pos.txt"
        self.session_data = SessionData(username=user, remote_loc=remote_loc, remote_loc_pet=remote_loc_pet,
                                        cluster_name=cluster_name, log_file=log_file, last_pos_file=last_pos_file)
        cookie.attach_to_response(response, self.session_id)
        await self.create_backend()

        return response

    async def create_backend(self):
        await backend.create(self.session_id, self.session_data)

    def get_backend(self):
        return backend.read(self.session_id)

    def delete_session(self, response=None):
        return cookie.delete_from_response(response)


    def get_session(self):
        return verifier.verify_session(self.session_data)


    def get_session_id(self):
        return self.session_id

    def get_session_data(self):
        return self.session_data
