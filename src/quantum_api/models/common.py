from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict[str, Any] | list[Any] | None = None
    request_id: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    qiskit_available: bool
    runtime_mode: str


class EchoTypeInfo(BaseModel):
    name: str
    description: str


class EchoTypesResponse(BaseModel):
    echo_types: list[EchoTypeInfo]


EndpointAuthMode = Literal["public", "api_key", "bearer_jwt"]


class PortfolioApiInfo(BaseModel):
    id: str
    name: str
    version: str
    icon: str
    description: str
    base_url: str = Field(alias="baseUrl")
    docs_url: str = Field(alias="docsUrl")
    health_url: str = Field(alias="healthUrl")
    status: str
    featured: bool = True
    tags: list[str]
    uptime: str

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class PortfolioEndpointParameter(BaseModel):
    name: str
    type: str
    required: bool
    description: str
    example: Any | None = None
    enum: list[str] | None = None
    depends_on: str | None = Field(default=None, alias="dependsOn")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class PortfolioEndpointRequestBody(BaseModel):
    description: str
    example: Any | None = None

    model_config = ConfigDict(extra="forbid")


class PortfolioEndpointResponse(BaseModel):
    code: str
    description: str
    example: Any | None = None

    model_config = ConfigDict(extra="forbid")


class PortfolioEndpoint(BaseModel):
    method: str
    path: str
    operation_path: str = Field(alias="operationPath")
    summary: str
    description: str | None = None
    auth: EndpointAuthMode
    parameters: list[PortfolioEndpointParameter] | None = None
    request_body: PortfolioEndpointRequestBody | None = Field(default=None, alias="requestBody")
    responses: list[PortfolioEndpointResponse]

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class PortfolioMetadataResponse(BaseModel):
    api: PortfolioApiInfo
    endpoints: list[PortfolioEndpoint]

    model_config = ConfigDict(extra="forbid")
