#pragma once

#include "CoreMinimal.h"
#include "QuantumApiTypes.h"

class IHttpRequest;
class IHttpResponse;

DECLARE_DELEGATE_OneParam(FQuantumApiErrorDelegate, const FQuantumApiError&)
DECLARE_DELEGATE_OneParam(FQuantumApiHealthDelegate, const FQuantumApiHealthResponse&)
DECLARE_DELEGATE_OneParam(FQuantumApiRunGateDelegate, const FQuantumApiRunGateResponse&)
DECLARE_DELEGATE_OneParam(FQuantumApiTextTransformDelegate, const FQuantumApiTextTransformResponse&)

class QUANTUMAPI_API FQuantumApiClient
{
public:
    explicit FQuantumApiClient(const class UQuantumApiSettings* InSettings);

    void HealthCheck(
        const FQuantumApiRequestOptions& Options,
        FQuantumApiHealthDelegate OnSuccess,
        FQuantumApiErrorDelegate OnError
    ) const;

    void RunGate(
        const FQuantumApiRunGateRequest& Request,
        const FQuantumApiRequestOptions& Options,
        FQuantumApiRunGateDelegate OnSuccess,
        FQuantumApiErrorDelegate OnError
    ) const;

    void TransformText(
        const FQuantumApiTextTransformRequest& Request,
        const FQuantumApiRequestOptions& Options,
        FQuantumApiTextTransformDelegate OnSuccess,
        FQuantumApiErrorDelegate OnError
    ) const;

private:
    FString BaseUrl;
    FString DefaultApiKey;
    FString DefaultBearerToken;
    EQuantumApiAuthMode AuthMode;
    float RequestTimeoutSeconds;

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> BuildRequest(
        const FString& Path,
        const FString& Verb,
        const FString& Body,
        const FQuantumApiRequestOptions& Options
    ) const;

    static FQuantumApiError BuildTransportError(const FString& Message);
    static FQuantumApiError BuildResponseError(const FHttpResponsePtr& Response);
    static TMap<FString, FString> ExtractHeaders(const FHttpResponsePtr& Response);
};
