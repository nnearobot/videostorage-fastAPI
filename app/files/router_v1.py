import hashlib
import os
from datetime import datetime

import aiofiles
from fastapi import APIRouter, Depends, UploadFile, status, Response
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import (ALLOWED_FILE_MAX_SIZE, ALLOWED_FILE_TYPES, CHUNK_SIZE,
                        STORAGE_DIR)
from app.database import get_async_session
from app.files.models import file_table
from app.files.schemas_v1 import FileList
from app.utils import Paginator

ROUT_PREFIX = "/files"

router = APIRouter(
    prefix=ROUT_PREFIX,
    tags=["files"],
)

# LIST FILES
@router.get("/", response_model=list[FileList], status_code=status.HTTP_200_OK)
async def list_uploaded_files(pagination: Paginator = Depends(Paginator), session: AsyncSession = Depends(get_async_session)) -> list[FileList]:
    query = select(file_table).filter(file_table.c.deleted == False)
    if pagination.limit > 0:
        query = query.offset(pagination.skip).limit(pagination.limit)
    result = await session.execute(query)
    return [FileList(
        fileid=file_db.fileid,
        name=file_db.name,
        size=file_db.size,
        created_at=file_db.created_at        
    ).dict() for file_db in result.all()]


# UPLOAD FILE
@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile, response: Response, session: AsyncSession = Depends(get_async_session)):
    # Check if file is provided:
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bad request"
        )

    # Check if file is of supported media type:
    if len(ALLOWED_FILE_TYPES) > 0 and file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported Media Type"
        )

    # Check if file is not too large:
    if ALLOWED_FILE_MAX_SIZE > 0 and file.size > ALLOWED_FILE_MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File is too large"
        )

    # By default fileid is an original name of the file.
    # If uploaded file has a name that already exists in a DB, then make a different fileid.

    # Check if the file with a specified fileid not yet exists in DB:
    file_id = file.filename
    file_db = await get_by_fileid(file_id, session)
    if file_db != None:
        # If we prefer to raise an exception about the file with the same name, uncomment lines below:
        """
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="File exists"
        )
        """
        # Make a new fileid by adding a '_1' to the file name.
        # If new fileid is also exists in DB, make a new one by adding a '_2' and so on.
        splitted_filename = os.path.splitext(file.filename)
        count = 1
        while True:
            new_file_id = "{}_{}{}".format(splitted_filename[0], count, splitted_filename[1])
            file_db = await get_by_fileid(new_file_id, session)
            count += 1
            if file_db is None:
                file_id = new_file_id
                break

    # Save file to the storage directory with a new name:
    new_filename = "{}_{}".format(datetime.now().strftime("%Y%m%d_%H%M%S"), file_id)
    save_path = os.path.join(STORAGE_DIR, new_filename)

    # We going to use Apache2 library aiofiles for asynchronous versions of files,
    # that support delegating operations to a separate thread pool.
    # Also we going to calculate the checksum of the file for integrity checking purpoise.
    hash = hashlib.sha256()
    try:
        async with aiofiles.open(save_path, 'wb') as f:
            while chunk := file.file.read(CHUNK_SIZE):
                hash.update(chunk)
                await f.write(chunk)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="There was an error uploading the file"
        )
    finally:
        await file.close()

    # Now save the data to the DB:
    stmt = insert(file_table).values(
        fileid=file_id,
        path=new_filename,
        # we going to restore this file name when download the file
        name=file.filename,
        size=file.size,
        checksum=hash.hexdigest(),
        mime=file.content_type,
        created_at=datetime.now()
    )
    await session.execute(stmt)
    await session.commit()

    response.headers["Location"] = "{}/{}".format(ROUT_PREFIX, file_id)

    return "File uploaded"


# DOWNLOAD FILE
@router.get("/{fileid}", status_code=status.HTTP_200_OK)
async def download_file(fileid: str, session: AsyncSession = Depends(get_async_session)):
    db_file = await get_by_fileid(fileid, session)
    if db_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    file_path = os.path.join(STORAGE_DIR, db_file.path)
    return FileResponse(
        path=file_path,
        media_type=db_file.mime,
        filename=db_file.name
    )


# DELETE FILE
@router.delete("/{fileid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(fileid: str, session: AsyncSession = Depends(get_async_session)):
    db_file = await get_by_fileid(fileid, session)
    if db_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Remove the file:
    file_path = os.path.join(STORAGE_DIR, db_file.path)
    os.remove(file_path)

    # Update a DB - mark the record deleted:
    stmt = (
        update(file_table)
        .values(deleted=True)
        .where(file_table.c.fileid == fileid)
    )
    await session.execute(stmt)
    await session.commit()
    return {"Description": "File was successfully removed"}


async def get_by_fileid(fileid: str, session: AsyncSession = Depends(get_async_session)):
    query = select(file_table).filter(file_table.c.fileid == fileid, file_table.c.deleted == False)
    result = await session.execute(query)
    return result.first()
