import threading

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
    session_data = SessionData(username=user, id=session_uuid, remote_loc=remote_loc, remote_loc_pet=remote_loc_pet,
                               cluster_name=cluster_name, log_file=log_file, last_pos_file=last_pos_file)
    cookie.attach_to_response(response, session_uuid)
    await backend.create(session_uuid, session_data)
    return session_uuid

async def set_job_id(session_uuid: UUID, session_data: SessionData, job_id):
    user = session_data.username
    remote_loc = session_data.remote_loc
    remote_loc_pet = session_data.remote_loc_pet
    cluster_name = session_data.cluster_name
    log_file = session_data.log_file
    last_pos_file = session_data.last_pos_file
    new_data = SessionData(username = user, id = session_uuid, remote_loc = remote_loc, remote_loc_pet = remote_loc_pet,
                           cluster_name = cluster_name, log_file = log_file, last_pos_file = last_pos_file,
                           job_id = job_id)
    await backend.update(session_uuid, new_data)
async def set_event(session_uuid: UUID, session_data: SessionData, event: bool):
    user = session_data.username
    remote_loc = session_data.remote_loc
    remote_loc_pet = session_data.remote_loc_pet
    cluster_name = session_data.cluster_name
    log_file = session_data.log_file
    last_pos_file = session_data.last_pos_file
    job_id = session_data.job_id

    new_data = SessionData(username = user, id=session_uuid, remote_loc = remote_loc, remote_loc_pet = remote_loc_pet,
                           cluster_name = cluster_name, log_file = log_file, last_pos_file = last_pos_file,
                           job_id = job_id, event = event)
    await backend.update(session_uuid, new_data)


async def set_job_status(session_uuid: UUID, session_data: SessionData, job_status, event: bool):
    user = session_data.username
    remote_loc = session_data.remote_loc
    remote_loc_pet = session_data.remote_loc_pet
    cluster_name = session_data.cluster_name
    log_file = session_data.log_file
    last_pos_file = session_data.last_pos_file
    job_id = session_data.job_id
    new_data = SessionData(username = user, id=session_uuid, remote_loc = remote_loc, remote_loc_pet = remote_loc_pet,
                           cluster_name = cluster_name, log_file = log_file, last_pos_file = last_pos_file,
                           job_id = job_id, event = event, job_status = job_status)
    await backend.update(session_uuid, new_data)


async def get_session(session_uuid):
    session = await backend.read(session_uuid)
    return session

async def end_session(cookie, response):
    cookie.delete_from_response(response)

