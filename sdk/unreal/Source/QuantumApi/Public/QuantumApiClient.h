// Copyright (c) 2026 David J. Grimsley. All rights reserved.
#pragma once

#include "CoreMinimal.h"
#include "QuantumApiTypes.h"

DECLARE_DELEGATE_OneParam(FQuantumApiErrorDelegate, const FQuantumApiError&)
DECLARE_DELEGATE_OneParam(FQuantumApiJsonDelegate, const FQuantumApiJsonResponse&)
DECLARE_DELEGATE_OneParam(FQuantumApiHealthDelegate, const FQuantumApiHealthResponse&)
DECLARE_DELEGATE_OneParam(FQuantumApiRunGateDelegate, const FQuantumApiRunGateResponse&)
DECLARE_DELEGATE_OneParam(FQuantumApiTextTransformDelegate, const FQuantumApiTextTransformResponse&)
DECLARE_DELEGATE_OneParam(FQuantumApiRandomIntDelegate, const FQuantumApiRandomIntResponse&)

/** Transport boundary used by the runtime HTTP adapter and UE Automation mocks. */
struct FQuantumApiTransportRequest
{
    FString Url;
    FString Verb;
    FString Body;
    float TimeoutSeconds = 10.0f;
    TMap<FString, FString> Headers;
};

struct FQuantumApiTransportResponse
{
    bool bConnectedSuccessfully = false;
    int32 StatusCode = 0;
    FString Body;
    TMap<FString, FString> Headers;
};

DECLARE_DELEGATE_OneParam(FQuantumApiTransportCompletion, const FQuantumApiTransportResponse&)

class QUANTUMAPI_API IQuantumApiTransport
{
public:
    virtual ~IQuantumApiTransport() = default;
    virtual void Send(const FQuantumApiTransportRequest& Request, FQuantumApiTransportCompletion Completion) = 0;
};

/**
 * Thread-safe, runtime-only HTTP client for the mounted Quantum API contract.
 * It never logs credentials and retries only read operations, avoiding duplicate jobs or random values.
 */
class QUANTUMAPI_API FQuantumApiClient
{
public:
    explicit FQuantumApiClient(const class UQuantumApiSettings* InSettings, TSharedPtr<IQuantumApiTransport> InTransport = nullptr);

    void HealthCheck(const FQuantumApiRequestOptions& Options, FQuantumApiHealthDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const;
    void GetEchoTypes(const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const;
    void RunGate(const FQuantumApiRunGateRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiRunGateDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const;
    void TransformText(const FQuantumApiTextTransformRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiTextTransformDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const;
    void GenerateRandomInt(const FQuantumApiRandomIntRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiRandomIntDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const;

    void RunCircuit(const FQuantumApiCircuitRunRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const;
    void ListBackends(const FQuantumApiBackendListRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const;
    void Transpile(const FQuantumApiTranspileRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const;
    void ImportQasm(const FQuantumApiQasmRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const;
    void ExportQasm(const FQuantumApiCircuitDefinition& Circuit, const FString& QasmVersion, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const;
    void RunQasm(const FQuantumApiQasmRunRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const;
    void SubmitCircuitJob(const FQuantumApiCircuitJobRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const;
    void SubmitQasmJob(const FQuantumApiQasmJobRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const;
    void SubmitRandomJob(const FQuantumApiRandomJobRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const;
    void GetJobStatus(const FString& JobId, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const;
    void GetJobResult(const FString& JobId, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const;
    void CancelJob(const FString& JobId, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const;
    void CallAdvanced(const FQuantumApiAdvancedRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const;

    /** Raw requests are public for native integrations, but protected endpoint paths are rejected. */
    void RequestJson(const FString& Path, const FString& Verb, const FString& Body, const FQuantumApiRequestOptions& Options, bool bCanRetry, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const;

    static bool TryGetAdvancedEndpoint(EQuantumApiAdvancedEndpoint Endpoint, FString& OutPath, FString& OutVerb);
    static bool ShouldRetryRequest(const FString& Verb, int32 StatusCode, int32 Attempt, int32 MaxReadRetries);
    static TSharedRef<class FJsonObject> SerializeCircuit(const FQuantumApiCircuitDefinition& Circuit);

private:
    FString BaseUrl;
    FString DefaultApiKey;
    FString DefaultIbmProfile;
    FString DefaultIbmHardwareBackend;
    EQuantumApiAuthMode AuthMode;
    float RequestTimeoutSeconds;
    int32 MaxReadRetries;
    float MaxRetryDelaySeconds;

    TSharedPtr<IQuantumApiTransport> Transport;

    FQuantumApiTransportRequest BuildTransportRequest(const FString& Path, const FString& Verb, const FString& Body, const FQuantumApiRequestOptions& Options) const;
    void DispatchRequest(const TSharedRef<struct FQuantumApiPendingRequest, ESPMode::ThreadSafe>& Pending) const;
    static FQuantumApiError BuildClientError(const FString& ErrorCode, const FString& Message);
    static FQuantumApiError BuildTransportError(const FString& Message);
    static FQuantumApiError BuildResponseError(const FQuantumApiTransportResponse& Response);
    static FQuantumApiResponseMeta BuildResponseMeta(const FQuantumApiTransportResponse& Response);
    static FString SerializeJsonObject(const TSharedRef<class FJsonObject>& JsonObject);
    static FString AppendQuery(const FString& Path, const TMap<FString, FString>& QueryParameters);
    FString ResolveIbmProfile(const FString& RequestProfile) const;
    FString ResolveIbmHardwareBackend(const FString& RequestBackendName) const;
    static bool ShouldUseDefaultIbmProfile(const FString& Provider, const FString& BackendName, bool bAssumeIbmProviderIfMissing);
    static bool IsProtectedPath(const FString& Path);
};
