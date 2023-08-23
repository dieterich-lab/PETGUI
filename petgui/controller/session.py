import petgui.dto.session
from fastapi import Request, APIRouter, Form, Response, Depends, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
import os
from uuid import uuid4
from petgui.dto.session import SessionData
from ..services.session import SessionService
import petgui.services.ldap as ldap
from petgui.controller import templating
import threading




session_router = APIRouter()
templates = Jinja2Templates(directory="templates")

local = False # If running app locally
ssh = "sshpass"
if local:
    ssh = "/opt/homebrew/bin/sshpass"

class User:
    session: SessionService
    job_id: str = None
    job_status: str
    event: threading.Event = None

@session_router.post("/login")
async def login(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    try:
        dn = ldap.get_dn_of_user(username)
        ldap.bind(dn, password)
        session = SessionService()
        print(response.headers)
        response = await session.create_session(username, response)  # Returns cookie
        request.app.state = User()
        request.app.state.session = session
        print(response.headers)
        session_uuid = session.get_session_id()
        os.environ[f"{hash(session_uuid)}"] = password
        os.makedirs(f"./{hash(session_uuid)}", exist_ok=True)  # If run with new conf.
        return RedirectResponse(url=request.url_for("whoami"), status_code=303, headers=response.headers)
    except Exception as e:
        print(str(e))
        error = 'Invalid username or password'
        return templating.login_form(request, error)


def get_cookies(request: Request):
    return request.cookies

def get_session_service(request: Request):
    return request.app.state.session

@session_router.get("/logout",  dependencies=[Depends(get_session_service)])
async def logout(request: Request, response: Response, cookie: str = Depends(get_cookies), session: SessionService = Depends(get_session_service)):
    # if request.app.state.event:
    #     request.app.state.event.set()   # Stop job threads
    #     request.app.state.event = None
    #await templating.clean(request, session, logout=True)
    if cookie and session:
        print(session.session_data)
        print(cookie)
        request.app.state = None
        session.delete_session(response)