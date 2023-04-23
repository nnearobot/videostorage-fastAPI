from dotenv import load_dotenv
import os
import sys

load_dotenv()

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")

DB_HOST_TEST = os.environ.get("DB_HOST_TEST")
DB_PORT_TEST = os.environ.get("DB_PORT_TEST")
DB_NAME_TEST = os.environ.get("DB_NAME_TEST")
DB_USER_TEST = os.environ.get("DB_USER_TEST")
DB_PASS_TEST = os.environ.get("DB_PASS_TEST")

# allowed media types (empty for no limit)
ALLOWED_FILE_TYPES = ["video/mp4", "video/mpeg"]

# max file size to upload (0 for no limit)
ALLOWED_FILE_MAX_SIZE = 1024 * 1024 * 1024 * 10  # = 10GB

STORAGE_DIR = os.path.join(sys.path[0], 'storage')
CHUNK_SIZE = 1024 * 1024
