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
        session = SessionService()
        request.app.state.session = await session.create_session(username, response)
        session_uuid = session.get_session_id()
        os.environ[f"{hash(session_uuid)}"] = password
        os.makedirs(f"./{hash(session_uuid)}", exist_ok=True)  # If run with new conf.
        return response
    except Exception as e:
        print(str(e))
        error = 'Invalid username or password'
        return templating.login_form(request, error)