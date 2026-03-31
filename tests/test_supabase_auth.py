from __future__ import annotations

import asyncio
import json
import time
from datetime import UTC, datetime, timedelta

import jwt
from cryptography.hazmat.primitives.asymmetric import ec

from quantum_api.config import Settings
from quantum_api.supabase_auth import SupabaseJwtVerifier


def test_verify_token_accepts_es256_jwk() -> None:
    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_jwt_issuer="https://example.supabase.co/auth/v1",
        supabase_jwt_audience="authenticated",
    )
    verifier = SupabaseJwtVerifier(settings)

    private_key = ec.generate_private_key(ec.SECP256R1())
    kid = "test-es256-kid"
    jwk = json.loads(jwt.algorithms.ECAlgorithm.to_jwk(private_key.public_key()))
    jwk["kid"] = kid
    jwk["alg"] = "ES256"

    verifier._jwks_by_kid = {kid: jwk}
    verifier._jwks_cached_at = time.time()

    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": "user-es256",
            "aud": "authenticated",
            "iss": "https://example.supabase.co/auth/v1",
            "email": "user@example.com",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        },
        private_key,
        algorithm="ES256",
        headers={"kid": kid, "alg": "ES256"},
    )

    try:
        user = asyncio.run(verifier.verify_token(token))
    finally:
        asyncio.run(verifier.close())

    assert user.user_id == "user-es256"
    assert user.email == "user@example.com"
