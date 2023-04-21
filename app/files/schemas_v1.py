from datetime import datetime
from pydantic import BaseModel

class FileList(BaseModel):
    fileid: str
    name: str
    size: int
    created_at: datetime

    class Config:
        orm_mode = True
