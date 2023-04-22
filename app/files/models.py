from datetime import datetime

from sqlalchemy import (TIMESTAMP, Boolean, Column, Index, Integer,
                        String, Table)

from app.database import metadata

file_table = Table(
    "files",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("fileid", String, nullable=False),
    Column("path", String, nullable=False),
    Column("name", String, nullable=False),
    Column("size", Integer, nullable=False),
    Column("checksum", String, nullable=False),
    Column("mime", String, nullable=False),
    Column("created_at", TIMESTAMP, default=datetime.now),
    Column("deleted", Boolean, default=False, nullable=False),
    Index("fileid", "fileid", unique = False)
)
