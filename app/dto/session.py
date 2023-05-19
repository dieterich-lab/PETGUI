from pydantic import BaseModel

class SessionData(BaseModel):
    username: str
    remote_loc: str
    remote_loc_pet: str
    cluster_name: str
    last_pos_file: str
    log_file: str
