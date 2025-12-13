"""RQ worker job functions.

RQ jobs are synchronous functions. We wrap our async pipeline with asyncio.run
inside the worker process.
"""

from __future__ import annotations

import asyncio

from app.services.document_processing import process_document


def process_document_job(document_id: str, user_id: str) -> None:
    asyncio.run(process_document(document_id=document_id, user_id=user_id))
