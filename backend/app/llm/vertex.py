"""Vertex AI Gemini helpers.

This module provides small wrappers around the Vertex AI Python SDK.
We keep it isolated so the rest of the app can choose a provider via config.

Auth:
- Preferred on Render: set GCP_SERVICE_ACCOUNT_JSON (full JSON string)
- Otherwise uses Application Default Credentials.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

from app.config import settings


_vertex_lock = asyncio.Lock()
_vertex_initialized = False


def _normalize_vertex_model_name(name: str) -> str:
    # If someone passes an AI Studio style name, strip the prefix.
    if name.startswith("models/"):
        return name.split("/", 1)[1]
    return name


def _load_credentials():
    if not settings.gcp_service_account_json:
        return None

    from google.oauth2 import service_account

    info = json.loads(settings.gcp_service_account_json)
    return service_account.Credentials.from_service_account_info(info)


async def ensure_vertex_initialized() -> None:
    global _vertex_initialized

    if _vertex_initialized:
        return

    async with _vertex_lock:
        if _vertex_initialized:
            return

        import vertexai

        if not settings.gcp_project_id:
            raise RuntimeError("GCP_PROJECT_ID is required when LLM_PROVIDER=vertex")

        creds = _load_credentials()
        if creds is None:
            vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)
        else:
            vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location, credentials=creds)

        _vertex_initialized = True


async def generate_text(
    prompt: str,
    model_name: str,
    *,
    temperature: float = 0.3,
    top_p: float = 0.8,
    top_k: int = 40,
    max_output_tokens: int = 2048,
) -> str:
    """Generate text using Vertex AI Gemini.

    Uses a thread offload because the Vertex SDK call is sync.
    """

    await ensure_vertex_initialized()

    import anyio
    from vertexai.generative_models import (
        GenerativeModel,
        GenerationConfig,
        SafetySetting,
        HarmCategory,
        HarmBlockThreshold,
    )

    vertex_model = _normalize_vertex_model_name(model_name)

    safety_settings = [
        SafetySetting(HarmCategory.HARM_CATEGORY_HARASSMENT, HarmBlockThreshold.BLOCK_ONLY_HIGH),
        SafetySetting(HarmCategory.HARM_CATEGORY_HATE_SPEECH, HarmBlockThreshold.BLOCK_ONLY_HIGH),
        SafetySetting(HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, HarmBlockThreshold.BLOCK_ONLY_HIGH),
        SafetySetting(HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, HarmBlockThreshold.BLOCK_ONLY_HIGH),
    ]

    config = GenerationConfig(
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        max_output_tokens=max_output_tokens,
    )

    def _call_sync() -> str:
        model = GenerativeModel(vertex_model)
        resp = model.generate_content(prompt, generation_config=config, safety_settings=safety_settings)
        # Vertex responses usually expose `.text`.
        return getattr(resp, "text", None) or str(resp)

    return await anyio.to_thread.run_sync(_call_sync)


async def embed_text(
    text: str,
    model_name: str,
    *,
    task_type: str,
) -> list[float]:
    """Embed a single text using Vertex text embedding models."""

    await ensure_vertex_initialized()

    import anyio

    from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

    vertex_model = _normalize_vertex_model_name(model_name)

    # Vertex expects task types like RETRIEVAL_QUERY / RETRIEVAL_DOCUMENT.
    task_type_norm = task_type.upper()

    def _call_sync() -> list[float]:
        model = TextEmbeddingModel.from_pretrained(vertex_model)
        inputs = [TextEmbeddingInput(text=text, task_type=task_type_norm)]
        embeddings = model.get_embeddings(inputs)
        if not embeddings:
            return [0.0] * 768
        return list(getattr(embeddings[0], "values", []))

    return await anyio.to_thread.run_sync(_call_sync)


async def embed_texts(
    texts: list[str],
    model_name: str,
    *,
    task_type: str,
) -> list[list[float]]:
    """Embed multiple texts using Vertex text embedding models."""

    await ensure_vertex_initialized()

    import anyio

    from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

    vertex_model = _normalize_vertex_model_name(model_name)
    task_type_norm = task_type.upper()

    def _call_sync() -> list[list[float]]:
        model = TextEmbeddingModel.from_pretrained(vertex_model)
        inputs = [TextEmbeddingInput(text=t, task_type=task_type_norm) for t in texts]
        embeddings = model.get_embeddings(inputs)
        vectors: list[list[float]] = []
        for emb in embeddings:
            vectors.append(list(getattr(emb, "values", [])))
        return vectors

    return await anyio.to_thread.run_sync(_call_sync)
