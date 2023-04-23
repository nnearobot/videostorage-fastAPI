import os
import sys

from httpx import AsyncClient
from fastapi import status

from app.config import (ALLOWED_FILE_MAX_SIZE, ALLOWED_FILE_TYPES, CHUNK_SIZE,
                        STORAGE_DIR)

TEST_FILES_DIR = os.path.join(os.getcwd(), 'test')

# Testing a /readyz endpoint
async def test_ready(ac: AsyncClient):
    response = await ac.get("/readyz")

    assert response.status_code == status.HTTP_200_OK


# Testing an empty request - should receive Bad request status
async def test_upload_no_file(ac: AsyncClient):
    response = await ac.post("/v1/files", files={'file': None})

    assert response.status_code == status.HTTP_400_BAD_REQUEST



# Testing an unsupported file uploading - should receive Unsupported media type status
async def test_upload_unsupported_file(ac: AsyncClient):
    test_file = os.path.join(TEST_FILES_DIR, 'post_4/test.txt')
    files = {'file': ('test.txt', open(test_file, "rb"), "text/javascript")}
    response = await ac.post("/v1/files", files=files)

    assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE



# Testing a correct file uploading
async def test_upload_file(ac: AsyncClient):
    test_file = os.path.join(TEST_FILES_DIR, 'post_1/sample.mp4')
    files = {'file': ('sample.mp4', open(test_file, "rb"), "video/mp4")}
    response = await ac.post("/v1/files", files=files)

    assert response.status_code == status.HTTP_201_CREATED
    assert "location" in response.headers
    assert response.headers["location"] == "/files/sample.mp4"



# Testing an uploading file with the existed name - should receive a location with another file id
async def test_upload_file_with_the_same_name(ac: AsyncClient):
    test_file = os.path.join(TEST_FILES_DIR, 'post_2/sample.mp4')
    files = {'file': ('sample.mp4', open(test_file, "rb"), "video/mp4")}
    response = await ac.post("/v1/files", files=files)

    assert response.headers["location"] == "/files/sample_1.mp4"



# Testing an uploading one more file with the existed name
async def test_upload_another_file_with_the_same_name(ac: AsyncClient):
    test_file = os.path.join(TEST_FILES_DIR, 'post_2/sample.mp4')
    files = {'file': ('sample.mp4', open(test_file, "rb"), "video/mp4")}
    response = await ac.post("/v1/files", files=files)

    assert response.headers["location"] == "/files/sample_2.mp4"



# Testing another content-type file uploading
async def test_upload_file_mpeg(ac: AsyncClient):
    test_file = os.path.join(TEST_FILES_DIR, 'post_3/sample.mpg')
    files = {'file': ('sample.mpg', open(test_file, "rb"), "video/mpeg")}
    response = await ac.post("/v1/files", files=files)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.headers["location"] == "/files/sample.mpg"



# Testing a file list retrieving - should receive a list with 4 items
async def test_get_file_list(ac: AsyncClient):
    response = await ac.get("/v1/files")
    file_list = response.json()

    assert type(file_list) == list
    assert len(file_list) == 4

    assert file_list[0]["fileid"] == "sample.mp4"
    assert file_list[1]["fileid"] == "sample_1.mp4"
    assert file_list[2]["fileid"] == "sample_2.mp4"
    assert file_list[3]["fileid"] == "sample.mpg"



# Testing a file downloading - should receive a file of size 2848208 bytes, not 11815175
async def test_download_file(ac: AsyncClient):
    response = await ac.get("/v1/files/sample.mp4")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-disposition"] == 'attachment; filename="sample.mp4"'
    assert response.headers["content-length"] == "2848208"
    assert response.headers["content-type"] == "video/mp4"



# Testing another file downloading - should receive a fie with content-type video/mpeg
async def test_download_another_file(ac: AsyncClient):
    response = await ac.get("/v1/files/sample.mpg")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "video/mpeg"



# Testing a non existing file downloading - should receive 404 status
async def test_download_non_existing_file(ac: AsyncClient):
    response = await ac.get("/v1/files/not_found.mp4")

    assert response.status_code == status.HTTP_404_NOT_FOUND



# Testing a file deleting
async def test_delete_files(ac: AsyncClient):
    response = await ac.delete("/v1/files/sample.mp4")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Check if file has been deleted:
    response = await ac.get("/v1/files/sample.mp4")
    assert response.status_code == status.HTTP_404_NOT_FOUND



# Testing a non existing file deleting - should receive 404 status
async def test_delete_non_existing_file(ac: AsyncClient):
    response = await ac.delete("/v1/files/not_found.mp4")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# Testing an empty list retrieving - should receive 0 items
async def test_get_file_list_when_empty(ac: AsyncClient):
    # delete all files so testing directory remains empty
    response = await ac.delete("/v1/files/sample_1.mp4")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = await ac.delete("/v1/files/sample_2.mp4")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = await ac.delete("/v1/files/sample.mpg")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = await ac.get("/v1/files")
    file_list = response.json()

    assert type(file_list) == list
    assert len(file_list) == 0
