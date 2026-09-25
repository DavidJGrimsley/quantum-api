#!/usr/bin/env python3
"""Deterministic local fixture for the Godot package-install harness."""

from __future__ import annotations

import json
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


class FixtureHandler(BaseHTTPRequestHandler):
    server_version = "QuantumGodotFixture/1.0"

    def log_message(self, _format: str, *_args: object) -> None:
        # Test output must not include request headers or bodies.
        return

    def _json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Request-Id", "fixture-request-id")
        self.end_headers()
        self.wfile.write(body)

    def _empty(self) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _malformed(self) -> None:
        body = b"this is not JSON"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _request_data(self) -> tuple[str, dict[str, list[str]], dict[str, object]]:
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length) if content_length else b""
        try:
            body = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except json.JSONDecodeError:
            body = {"_invalid_json": True}
        return parsed.path, parse_qs(parsed.query), body

    def _response_context(
        self, path: str, query: dict[str, list[str]], body: dict[str, object]
    ) -> dict[str, object]:
        return {
            "fixture": True,
            "path": path,
            "query": query,
            "body": body,
            "saw_api_key": bool(self.headers.get("X-API-Key")),
        }

    def do_GET(self) -> None:  # noqa: N802
        path, query, body = self._request_data()
        context = self._response_context(path, query, body)
        if path == "/v1/health":
            self._json(HTTPStatus.OK, {"status": "ok", **context})
            return
        if path == "/v1/list_backends":
            self._json(HTTPStatus.OK, {"backends": [], **context})
            return
        if path.startswith("/v1/jobs/") and path.endswith("/result"):
            self._json(HTTPStatus.OK, {"result": {"counts": {"1": 128}}, **context})
            return
        if path.startswith("/v1/jobs/"):
            self._json(HTTPStatus.OK, {"job_id": path.rsplit("/", 1)[-1], **context})
            return
        self._json(HTTPStatus.NOT_FOUND, {"error": "not_found", "message": "Fixture route not found."})

    def do_POST(self) -> None:  # noqa: N802
        path, query, body = self._request_data()
        context = self._response_context(path, query, body)
        if path == "/v1/text/transform":
            text = str(body.get("text", ""))
            if text == "fixture-empty":
                self._empty()
                return
            if text == "fixture-malformed":
                self._malformed()
                return
            if text == "fixture-timeout":
                time.sleep(1.0)
            if text == "fixture-unauthorized":
                self._json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized", "message": "Fixture unauthorized."})
                return
            if text == "fixture-rate-limit":
                self._json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "rate_limited", "message": "Fixture rate limited."})
                return
            if text == "fixture-server-error":
                self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "upstream_error", "message": "Fixture server error."})
                return
            self._json(HTTPStatus.OK, {"original": text, "transformed": "fixture:" + text, **context})
            return
        if path == "/v1/gates/run":
            if body.get("gate_type") == "rotation" and "rotation_angle_rad" not in body:
                self._json(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": "validation_error", "message": "rotation_angle_rad is required."})
                return
            self._json(HTTPStatus.OK, {"measurement": 1, "success": True, "superposition_strength": 0.5, **context})
            return
        if path == "/v1/topological/braid":
            braid_word = body.get("braid_word")
            initial_state = body.get("initial_state")
            if braid_word == [{"generator": 2, "power": 1}] and initial_state == "0":
                # Published TQSim fixed-total-tau reference for sigma_2 |0>.
                logical_state = [
                    {"real": -0.5, "imag": 0.3632712640026805},
                    {"real": -0.24293413587832285, "imag": -0.7476743906106105},
                ]
                probabilities = {"vacuum": 0.3819660112501051, "tau": 0.6180339887498949}
                outcome = "vacuum"
            elif braid_word == [] and initial_state == "1":
                logical_state = [{"real": 0.0, "imag": 0.0}, {"real": 1.0, "imag": 0.0}]
                probabilities = {"vacuum": 0.0, "tau": 1.0}
                outcome = "tau"
            else:
                self._json(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": "unsupported_fixture_braid"})
                return
            measure = body.get("measure") is True
            shots = body.get("shots", 0) if measure else 0
            self._json(HTTPStatus.OK, {
                "model": "fibonacci",
                "anyon_count": 3,
                "total_charge": "tau",
                "initial_state": initial_state,
                "braid_word": braid_word,
                "logical_state": logical_state,
                "fusion_probabilities": probabilities,
                "measurement": outcome if measure else None,
                "shots": shots,
                "counts": {"vacuum": shots if outcome == "vacuum" else 0, "tau": shots if outcome == "tau" else 0} if measure else None,
                "metadata": {
                    "simulation_type": "digital_simulation_of_fibonacci_braid",
                    "convention": "fixture",
                    "logical_dimension": 2,
                },
                **context,
            })
            return
        if path == "/v1/transpile":
            self._json(HTTPStatus.OK, {"transpiled": True, **context})
            return
        if path == "/v1/jobs/circuits":
            self._json(HTTPStatus.OK, {"job_id": "fixture-job", **context})
            return
        self._json(HTTPStatus.NOT_FOUND, {"error": "not_found", "message": "Fixture route not found."})


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 18101), FixtureHandler).serve_forever()
