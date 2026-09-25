from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import APIRouter, HTTPException, Request
from fastapi.routing import APIRoute
from starlette.responses import Response

from quantum_api.models.api import TopologicalBraidRequest, TopologicalBraidResponse
from quantum_api.services.topological.braid import run_topological_braid

_MAX_BRAID_BODY_BYTES = 65_536


class _BoundedJsonRoute(APIRoute):
    """Bound braid JSON before FastAPI parses a caller-controlled request body."""

    def get_route_handler(self) -> Callable[[Request], Awaitable[Response]]:
        route_handler = super().get_route_handler()

        async def bounded_json_handler(request: Request) -> Response:
            content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
            if content_type != "application/json":
                raise HTTPException(status_code=415, detail="Content-Type must be application/json.")

            content_length = request.headers.get("content-length")
            if content_length is not None:
                try:
                    declared_length = int(content_length)
                except ValueError as exc:
                    raise HTTPException(status_code=400, detail="Invalid Content-Length header.") from exc
                if declared_length > _MAX_BRAID_BODY_BYTES:
                    raise HTTPException(status_code=413, detail="Braid request body is too large.")

            chunks: list[bytes] = []
            received_bytes = 0
            async for chunk in request.stream():
                received_bytes += len(chunk)
                if received_bytes > _MAX_BRAID_BODY_BYTES:
                    raise HTTPException(status_code=413, detail="Braid request body is too large.")
                chunks.append(chunk)

            # Starlette's Request.body() cache lets the original FastAPI handler
            # parse the bounded bytes without reading the ASGI stream again.
            request._body = b"".join(chunks)
            return await route_handler(request)

        return bounded_json_handler


router = APIRouter(route_class=_BoundedJsonRoute)


@router.post("/topological/braid", response_model=TopologicalBraidResponse)
def topological_braid(request_data: TopologicalBraidRequest) -> TopologicalBraidResponse:
    """Evaluate a three-Fibonacci-anyon braid and optionally sample measurement."""

    return TopologicalBraidResponse.model_validate(run_topological_braid(request_data))
