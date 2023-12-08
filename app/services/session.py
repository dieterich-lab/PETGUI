from ..dto.session import SessionData, SessionCookie, BasicVerifier, CookieParameters, verifier, backend, cookie
from fastapi import Depends, HTTPException
from uuid import uuid4, UUID


async def create_session(user, response):
    session_uuid = uuid4()
    remote_loc = f"/home/{user}/{hash(session_uuid)}/"
    remote_loc_pet = f"/home/{user}/{hash(session_uuid)}/pet/"
    cluster_name = "cluster.dieterichlab.org"
    log_file = f"{hash(session_uuid)}/logging.txt"
    last_pos_file = f"{hash(session_uuid)}/last_pos.txt"
    session_data = SessionData(username=user, remote_loc=remote_loc, remote_loc_pet=remote_loc_pet,
                                    cluster_name=cluster_name, log_file=log_file, last_pos_file=last_pos_file)
    cookie.attach_to_response(response, session_uuid)
    await backend.create(session_uuid, session_data)
    return session_uuid


async def get_session(session_uuid):
    session = await backend.read(session_uuid)
    return session


async def end_session(response):
    cookie.delete_from_response(response)

