"""
chroma_proxy.py  —  /chroma-proxy/*
Proxies ChromaDB HTTP API calls so the browser (served from :8000)
can talk to Chroma (:8001) without CORS errors.
"""

import os
import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = os.getenv("CHROMA_PORT", "8001")
CHROMA_BASE = f"http://{CHROMA_HOST}:{CHROMA_PORT}"

router = APIRouter(prefix="/chroma-proxy", tags=["chroma-proxy"])


@router.api_route("/api/{version}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def chroma_proxy(version: str, path: str, request: Request):
    """Forward any /chroma-proxy/api/* request to the Chroma server."""
    url = f"{CHROMA_BASE}/api/{version}/{path}"

    body = await request.body()
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=url,
                content=body,
                headers=headers,
                params=dict(request.query_params),
            )
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                media_type=resp.headers.get("content-type", "application/json"),
            )
        except httpx.ConnectError:
            return JSONResponse(
                status_code=503,
                content={"detail": f"Cannot reach Chroma at {CHROMA_BASE}. Is it running?"},
            )
