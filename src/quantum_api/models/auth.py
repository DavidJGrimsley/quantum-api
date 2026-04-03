from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ApiKeyPolicyResponse(BaseModel):
    rate_limit_per_second: int = Field(ge=1)
    rate_limit_per_minute: int = Field(ge=1)
    daily_quota: int = Field(ge=1)

    model_config = ConfigDict(extra="forbid")


class ApiKeyMetadataResponse(BaseModel):
    key_id: str
    owner_user_id: str
    name: str | None = None
    key_prefix: str
    masked_key: str
    status: str
    policy: ApiKeyPolicyResponse
    created_at: datetime
    revoked_at: datetime | None = None
    rotated_from_id: str | None = None
    rotated_to_id: str | None = None
    last_used_at: datetime | None = None

    model_config = ConfigDict(extra="forbid")


class ApiKeyListResponse(BaseModel):
    keys: list[ApiKeyMetadataResponse]

    model_config = ConfigDict(extra="forbid")


class ApiKeyCreateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=128)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"name": "Portfolio demo key"}},
    )


class ApiKeyCreateResponse(BaseModel):
    key: ApiKeyMetadataResponse
    raw_key: str
    secret_visible_once: bool = True

    model_config = ConfigDict(extra="forbid")


class ApiKeyRevokeResponse(BaseModel):
    key: ApiKeyMetadataResponse

    model_config = ConfigDict(extra="forbid")


class ApiKeyRotateResponse(BaseModel):
    previous_key: ApiKeyMetadataResponse
    new_key: ApiKeyMetadataResponse
    raw_key: str
    secret_visible_once: bool = True

    model_config = ConfigDict(extra="forbid")


class ApiKeyDeleteResponse(BaseModel):
    deleted_key_id: str
    deleted: bool = True

    model_config = ConfigDict(extra="forbid")


class ApiKeyDeleteRevokedResponse(BaseModel):
    deleted_count: int = Field(ge=0)

    model_config = ConfigDict(extra="forbid")


IBMChannel = Literal["ibm_quantum_platform", "ibm_cloud"]


class IBMProfileResponse(BaseModel):
    profile_id: str
    owner_user_id: str
    profile_name: str
    instance: str
    channel: IBMChannel
    masked_token: str
    is_default: bool
    verification_status: Literal["unverified", "verified", "invalid"]
    last_verified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


class IBMProfileListResponse(BaseModel):
    profiles: list[IBMProfileResponse]

    model_config = ConfigDict(extra="forbid")


class IBMProfileCreateRequest(BaseModel):
    profile_name: str = Field(min_length=1, max_length=128)
    token: str = Field(min_length=1)
    instance: str = Field(min_length=1)
    channel: IBMChannel = "ibm_quantum_platform"
    is_default: bool = False

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "profile_name": "IBM Open",
                "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "instance": "crn:v1:bluemix:public:quantum-computing:us-east:a/example::",
                "channel": "ibm_quantum_platform",
                "is_default": True,
            }
        },
    )


class IBMProfileUpdateRequest(BaseModel):
    profile_name: str | None = Field(default=None, min_length=1, max_length=128)
    token: str | None = Field(default=None, min_length=1)
    instance: str | None = Field(default=None, min_length=1)
    channel: IBMChannel | None = None
    is_default: bool | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_has_update(self) -> IBMProfileUpdateRequest:
        if (
            self.profile_name is None
            and self.token is None
            and self.instance is None
            and self.channel is None
            and self.is_default is None
        ):
            raise ValueError("at least one field must be provided")
        return self


class IBMProfileVerifyResponse(BaseModel):
    profile: IBMProfileResponse
    verified: bool = True

    model_config = ConfigDict(extra="forbid")
