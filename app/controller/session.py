from fastapi import Request, APIRouter, Form, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
import os
from uuid import uuid4
from app.dto.session import SessionData
from ..services.session import SessionService
import app.services.ldap as ldap
from app.controller import templating


session_router = APIRouter()
templates = Jinja2Templates(directory="templates")

local = False # If running app locally
ssh = "sshpass"
if local:
    ssh = "/opt/homebrew/bin/sshpass"


@session_router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        dn = ldap.get_dn_of_user(username)
        ldap.bind(dn, password)
        response = RedirectResponse(url=request.url_for("homepage"), status_code=303)
        session = await create_session(request, username, response)
        session_uuid = session.get_session_id()
        os.environ[f"{hash(session_uuid)}"] = password
        os.makedirs(f"./{hash(session_uuid)}", exist_ok=True)  # If run with new conf.
        return response
    except Exception as e:
        print(str(e))
        error = 'Invalid username or password'
        return await templating.login_form(request, error)

async def create_session(request: Request, user: str, response: Response):
    session_id = uuid4()
    remote_loc = f"/home/{user}/{hash(session_id)}/"
    remote_loc_pet = f"/home/{user}/{hash(session_id)}/pet/"
    cluster_name = "cluster.dieterichlab.org"
    log_file = f"{hash(session_id)}/logging.txt"
    last_pos_file = f"{hash(session_id)}/last_pos.txt"
    data = SessionData(username=user, remote_loc=remote_loc, remote_loc_pet=remote_loc_pet, cluster_name=cluster_name,
                       log_file=log_file, last_pos_file=last_pos_file)
    request.app.state.session = SessionService(data, session_id)
    session = request.app.state.session
    session.create_cookie(response=response)
    await session.create_backend()
    return session
