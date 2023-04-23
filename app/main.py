from fastapi import FastAPI, status
from app.files.router_v1 import router as file_router_v1


app = FastAPI(
    title="Video Storage Server API"
)


@app.get("/v1/readyz", status_code=status.HTTP_200_OK)
def is_ready():
    return {"Description": "OK"}

app.include_router(file_router_v1)
app.include_router(file_router_v1, prefix="/v1")


"""
When we will need some new features, which break v1 functionality,
we can create a new subpackage, e.g. v2, and include its routers:

from app.v2.file.router import router as file_router_v2

app.include_router(file_router_v1, prefix="/v1")

app.include_router(file_router_v2)
app.include_router(file_router_v2.router, prefix="/v2")

"""