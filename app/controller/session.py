from fastapi import Request, APIRouter, Form, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import os
from app.services.session import create_session
from app.services.ldap import LDAP
from app.controller import templating

session_router = APIRouter()
templates = Jinja2Templates(directory="templates")

local = False # If running app locally
ssh = "sshpass"
if local:
    ssh = "/opt/homebrew/bin/sshpass"


@session_router.post("/login")
async def login(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    try:
        ldap = LDAP()
        dn = ldap.get_dn_of_user(username)
        ldap.bind(dn, password)
        session_uuid = await create_session(username, response)
        response.delete_cookie(key="cookie")
        response.set_cookie(key="session", value=session_uuid)
        os.environ[f"{hash(session_uuid)}"] = password
        return RedirectResponse(url=request.url_for("homepage"), status_code=303, headers=response.headers)

    except Exception as e:
        print(str(e))
        error = 'Invalid username or password'
        return templating.login_form(request, error)
