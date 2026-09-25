// Copyright (c) 2026 David J. Grimsley. All rights reserved.
#include "QuantumApiClient.h"

#include "Containers/Ticker.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "GenericPlatform/GenericPlatformHttp.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "JsonObjectConverter.h"
#include "QuantumApiSettings.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

struct FQuantumApiPendingRequest
{
    FString Path;
    FString Verb;
    FString Body;
    FQuantumApiRequestOptions Options;
    bool bCanRetry = false;
    int32 Attempt = 0;
    FQuantumApiJsonDelegate OnSuccess;
    FQuantumApiErrorDelegate OnError;
};

namespace
{
TMap<FString, FString> GetResponseHeaders(const FHttpResponsePtr& Response)
{
    TMap<FString, FString> Headers;
    if (!Response.IsValid()) return Headers;
    for (const FString& HeaderLine : Response->GetAllHeaders())
    {
        FString Key;
        FString Value;
        if (HeaderLine.Split(TEXT(":"), &Key, &Value)) Headers.Add(Key.TrimStartAndEnd(), Value.TrimStartAndEnd());
    }
    return Headers;
}

const FString* FindHeaderValue(const TMap<FString, FString>& Headers, const TCHAR* HeaderName)
{
    for (const TPair<FString, FString>& Header : Headers)
    {
        if (Header.Key.Equals(HeaderName, ESearchCase::IgnoreCase)) return &Header.Value;
    }
    return nullptr;
}

class FQuantumApiHttpTransport final : public IQuantumApiTransport
{
public:
    virtual void Send(const FQuantumApiTransportRequest& Request, FQuantumApiTransportCompletion Completion) override
    {
        const TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest = FHttpModule::Get().CreateRequest();
        HttpRequest->SetURL(Request.Url);
        HttpRequest->SetVerb(Request.Verb);
        HttpRequest->SetTimeout(Request.TimeoutSeconds);
        for (const TPair<FString, FString>& Header : Request.Headers)
        {
            HttpRequest->SetHeader(Header.Key, Header.Value);
        }
        if (!Request.Body.IsEmpty()) HttpRequest->SetContentAsString(Request.Body);

        HttpRequest->OnProcessRequestComplete().BindLambda([Completion](FHttpRequestPtr, FHttpResponsePtr Response, bool bConnectedSuccessfully)
        {
            FQuantumApiTransportResponse TransportResponse;
            TransportResponse.bConnectedSuccessfully = bConnectedSuccessfully;
            TransportResponse.StatusCode = Response.IsValid() ? Response->GetResponseCode() : 0;
            TransportResponse.Body = Response.IsValid() ? Response->GetContentAsString() : TEXT("");
            TransportResponse.Headers = GetResponseHeaders(Response);
            Completion.ExecuteIfBound(TransportResponse);
        });

        if (!HttpRequest->ProcessRequest())
        {
            FQuantumApiTransportResponse TransportResponse;
            Completion.ExecuteIfBound(TransportResponse);
        }
    }
};

void SetCircuitField(const TSharedRef<FJsonObject>& JsonObject, const FQuantumApiCircuitDefinition& Circuit)
{
    JsonObject->SetObjectField(TEXT("circuit"), FQuantumApiClient::SerializeCircuit(Circuit));
}

void SetOptionalString(const TSharedRef<FJsonObject>& JsonObject, const TCHAR* FieldName, const FString& Value)
{
    if (!Value.IsEmpty())
    {
        JsonObject->SetStringField(FieldName, Value);
    }
}
}

FQuantumApiClient::FQuantumApiClient(const UQuantumApiSettings* InSettings, TSharedPtr<IQuantumApiTransport> InTransport)
    : BaseUrl(InSettings ? InSettings->GetResolvedBaseUrl() : TEXT(""))
    , DefaultApiKey(InSettings ? InSettings->ApiKey : TEXT(""))
    , DefaultIbmProfile(InSettings ? InSettings->GetDefaultIbmProfile() : TEXT(""))
    , DefaultIbmHardwareBackend(InSettings ? InSettings->GetDefaultIbmHardwareBackend() : TEXT(""))
    , AuthMode(InSettings ? InSettings->AuthMode : EQuantumApiAuthMode::DirectApiKey)
    , RequestTimeoutSeconds(InSettings ? InSettings->RequestTimeoutSeconds : 10.0f)
    , MaxReadRetries(InSettings ? InSettings->MaxReadRetries : 2)
    , MaxRetryDelaySeconds(InSettings ? InSettings->MaxRetryDelaySeconds : 5.0f)
    , Transport(MoveTemp(InTransport))
{
    if (!Transport)
    {
        Transport = MakeShared<FQuantumApiHttpTransport>();
    }
}

void FQuantumApiClient::HealthCheck(const FQuantumApiRequestOptions& Options, FQuantumApiHealthDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const
{
    RequestJson(TEXT("/health"), TEXT("GET"), TEXT(""), Options, true,
        FQuantumApiJsonDelegate::CreateLambda([OnSuccess, OnError](const FQuantumApiJsonResponse& Raw)
        {
            FQuantumApiHealthResponse Payload;
            if (!FJsonObjectConverter::JsonObjectStringToUStruct(Raw.Json, &Payload, 0, 0))
            {
                OnError.ExecuteIfBound(BuildTransportError(TEXT("Failed to parse health response JSON.")));
                return;
            }
            Payload.Meta = Raw.Meta;
            OnSuccess.ExecuteIfBound(Payload);
        }), OnError);
}

void FQuantumApiClient::GetEchoTypes(const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const
{
    RequestJson(TEXT("/echo-types"), TEXT("GET"), TEXT(""), Options, true, MoveTemp(OnSuccess), MoveTemp(OnError));
}

void FQuantumApiClient::RunGate(const FQuantumApiRunGateRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiRunGateDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const
{
    const TSharedRef<FJsonObject> JsonObject = MakeShared<FJsonObject>();
    JsonObject->SetStringField(TEXT("gate_type"), Request.GateType);
    if (Request.bSendRotationAngle)
    {
        JsonObject->SetNumberField(TEXT("rotation_angle_rad"), Request.RotationAngleRad);
    }

    RequestJson(TEXT("/gates/run"), TEXT("POST"), SerializeJsonObject(JsonObject), Options, false,
        FQuantumApiJsonDelegate::CreateLambda([OnSuccess, OnError](const FQuantumApiJsonResponse& Raw)
        {
            FQuantumApiRunGateResponse Payload;
            if (!FJsonObjectConverter::JsonObjectStringToUStruct(Raw.Json, &Payload, 0, 0))
            {
                OnError.ExecuteIfBound(BuildTransportError(TEXT("Failed to parse gate response JSON.")));
                return;
            }
            Payload.Meta = Raw.Meta;
            OnSuccess.ExecuteIfBound(Payload);
        }), OnError);
}

void FQuantumApiClient::TransformText(const FQuantumApiTextTransformRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiTextTransformDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const
{
    const TSharedRef<FJsonObject> JsonObject = MakeShared<FJsonObject>();
    JsonObject->SetStringField(TEXT("text"), Request.Text);
    RequestJson(TEXT("/text/transform"), TEXT("POST"), SerializeJsonObject(JsonObject), Options, false,
        FQuantumApiJsonDelegate::CreateLambda([OnSuccess, OnError](const FQuantumApiJsonResponse& Raw)
        {
            FQuantumApiTextTransformResponse Payload;
            if (!FJsonObjectConverter::JsonObjectStringToUStruct(Raw.Json, &Payload, 0, 0))
            {
                OnError.ExecuteIfBound(BuildTransportError(TEXT("Failed to parse text transformation response JSON.")));
                return;
            }
            Payload.Meta = Raw.Meta;
            OnSuccess.ExecuteIfBound(Payload);
        }), OnError);
}

void FQuantumApiClient::GenerateRandomInt(const FQuantumApiRandomIntRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiRandomIntDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const
{
    if (Request.Min > Request.Max)
    {
        OnError.ExecuteIfBound(BuildClientError(TEXT("invalid_request"), TEXT("Min must be less than or equal to Max.")));
        return;
    }

    const TSharedRef<FJsonObject> JsonObject = MakeShared<FJsonObject>();
    JsonObject->SetNumberField(TEXT("min"), Request.Min);
    JsonObject->SetNumberField(TEXT("max"), Request.Max);
    RequestJson(TEXT("/random"), TEXT("POST"), SerializeJsonObject(JsonObject), Options, false,
        FQuantumApiJsonDelegate::CreateLambda([OnSuccess, OnError](const FQuantumApiJsonResponse& Raw)
        {
            FQuantumApiRandomIntResponse Payload;
            if (!FJsonObjectConverter::JsonObjectStringToUStruct(Raw.Json, &Payload, 0, 0))
            {
                OnError.ExecuteIfBound(BuildTransportError(TEXT("Failed to parse random response JSON.")));
                return;
            }
            Payload.Meta = Raw.Meta;
            OnSuccess.ExecuteIfBound(Payload);
        }), OnError);
}

void FQuantumApiClient::RunCircuit(const FQuantumApiCircuitRunRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const
{
    const TSharedRef<FJsonObject> JsonObject = SerializeCircuit(Request.Circuit);
    JsonObject->SetNumberField(TEXT("shots"), Request.Shots);
    JsonObject->SetBoolField(TEXT("include_statevector"), Request.bIncludeStatevector);
    if (Request.bSendSeed) JsonObject->SetNumberField(TEXT("seed"), Request.Seed);
    RequestJson(TEXT("/circuits/run"), TEXT("POST"), SerializeJsonObject(JsonObject), Options, false, MoveTemp(OnSuccess), MoveTemp(OnError));
}

void FQuantumApiClient::EvaluateTopologicalBraid(const FQuantumApiTopologicalBraidRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const
{
    if (Request.AnyonCount != 3)
    {
        OnError.ExecuteIfBound(BuildClientError(TEXT("invalid_request"), TEXT("Topological braid v1 currently requires Anyon Count = 3.")));
        return;
    }

    const TSharedRef<FJsonObject> JsonObject = MakeShared<FJsonObject>();
    JsonObject->SetStringField(TEXT("model"), Request.Model.IsEmpty() ? TEXT("fibonacci") : Request.Model);
    JsonObject->SetNumberField(TEXT("anyon_count"), Request.AnyonCount);
    JsonObject->SetStringField(TEXT("total_charge"), Request.TotalCharge.IsEmpty() ? TEXT("tau") : Request.TotalCharge);
    JsonObject->SetStringField(TEXT("initial_state"), Request.InitialState.IsEmpty() ? TEXT("0") : Request.InitialState);
    JsonObject->SetBoolField(TEXT("measure"), Request.bMeasure);
    JsonObject->SetNumberField(TEXT("shots"), FMath::Clamp(Request.Shots, 0, 4096));
    if (Request.bSendSeed)
    {
        JsonObject->SetNumberField(TEXT("seed"), Request.Seed);
    }

    TArray<TSharedPtr<FJsonValue>> BraidWord;
    for (const FQuantumApiBraidOperation& Operation : Request.BraidWord)
    {
        if ((Operation.Generator != 1 && Operation.Generator != 2) || (Operation.Power != 1 && Operation.Power != -1))
        {
            OnError.ExecuteIfBound(BuildClientError(TEXT("invalid_request"), TEXT("Each braid operation requires Generator 1 or 2 and Power 1 or -1.")));
            return;
        }

        const TSharedRef<FJsonObject> Item = MakeShared<FJsonObject>();
        Item->SetNumberField(TEXT("generator"), Operation.Generator);
        Item->SetNumberField(TEXT("power"), Operation.Power);
        BraidWord.Add(MakeShared<FJsonValueObject>(Item));
    }
    JsonObject->SetArrayField(TEXT("braid_word"), BraidWord);

    RequestJson(TEXT("/topological/braid"), TEXT("POST"), SerializeJsonObject(JsonObject), Options, false, MoveTemp(OnSuccess), MoveTemp(OnError));
}

void FQuantumApiClient::ListBackends(const FQuantumApiBackendListRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const
{
    TMap<FString, FString> Query;
    if (!Request.Provider.IsEmpty()) Query.Add(TEXT("provider"), Request.Provider);
    Query.Add(TEXT("simulator_only"), Request.bSimulatorOnly ? TEXT("true") : TEXT("false"));
    Query.Add(TEXT("min_qubits"), FString::FromInt(FMath::Max(1, Request.MinQubits)));
    const FString IbmProfile = ResolveIbmProfile(Request.IbmProfile);
    if (!IbmProfile.IsEmpty() && (Request.Provider.Equals(TEXT("ibm"), ESearchCase::IgnoreCase) || !Request.IbmProfile.IsEmpty()))
    {
        Query.Add(TEXT("ibm_profile"), IbmProfile);
    }
    RequestJson(AppendQuery(TEXT("/list_backends"), Query), TEXT("GET"), TEXT(""), Options, true, MoveTemp(OnSuccess), MoveTemp(OnError));
}

void FQuantumApiClient::Transpile(const FQuantumApiTranspileRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const
{
    FString BackendName = Request.BackendName;
    BackendName.TrimStartAndEndInline();
    if (BackendName.IsEmpty() && (Request.Provider.IsEmpty() || Request.Provider.Equals(TEXT("ibm"), ESearchCase::IgnoreCase)))
    {
        BackendName = ResolveIbmHardwareBackend(Request.BackendName);
    }
    if (BackendName.IsEmpty())
    {
        OnError.ExecuteIfBound(BuildClientError(TEXT("invalid_request"), TEXT("Transpile requires a Backend Name or a configured Default IBM Hardware Backend.")));
        return;
    }
    const TSharedRef<FJsonObject> JsonObject = MakeShared<FJsonObject>();
    JsonObject->SetStringField(TEXT("backend_name"), BackendName);
    JsonObject->SetNumberField(TEXT("optimization_level"), Request.OptimizationLevel);
    JsonObject->SetStringField(TEXT("output_qasm_version"), Request.OutputQasmVersion);
    SetOptionalString(JsonObject, TEXT("provider"), Request.Provider);
    const FString IbmProfile = ShouldUseDefaultIbmProfile(Request.Provider, BackendName, false) ? ResolveIbmProfile(Request.IbmProfile) : Request.IbmProfile;
    SetOptionalString(JsonObject, TEXT("ibm_profile"), IbmProfile);
    if (Request.bSendSeedTranspiler) JsonObject->SetNumberField(TEXT("seed_transpiler"), Request.SeedTranspiler);
    if (Request.bUseQasmInput)
    {
        const TSharedRef<FJsonObject> Qasm = MakeShared<FJsonObject>();
        Qasm->SetStringField(TEXT("source"), Request.Qasm);
        Qasm->SetStringField(TEXT("qasm_version"), Request.QasmVersion);
        JsonObject->SetObjectField(TEXT("qasm"), Qasm);
    }
    else
    {
        SetCircuitField(JsonObject, Request.Circuit);
    }
    RequestJson(TEXT("/transpile"), TEXT("POST"), SerializeJsonObject(JsonObject), Options, false, MoveTemp(OnSuccess), MoveTemp(OnError));
}

void FQuantumApiClient::ImportQasm(const FQuantumApiQasmRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const
{
    const TSharedRef<FJsonObject> JsonObject = MakeShared<FJsonObject>();
    JsonObject->SetStringField(TEXT("qasm"), Request.Qasm);
    JsonObject->SetStringField(TEXT("qasm_version"), Request.QasmVersion);
    RequestJson(TEXT("/qasm/import"), TEXT("POST"), SerializeJsonObject(JsonObject), Options, false, MoveTemp(OnSuccess), MoveTemp(OnError));
}

void FQuantumApiClient::ExportQasm(const FQuantumApiCircuitDefinition& Circuit, const FString& QasmVersion, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const
{
    const TSharedRef<FJsonObject> JsonObject = MakeShared<FJsonObject>();
    SetCircuitField(JsonObject, Circuit);
    JsonObject->SetStringField(TEXT("qasm_version"), QasmVersion.IsEmpty() ? TEXT("3") : QasmVersion);
    RequestJson(TEXT("/qasm/export"), TEXT("POST"), SerializeJsonObject(JsonObject), Options, false, MoveTemp(OnSuccess), MoveTemp(OnError));
}

void FQuantumApiClient::RunQasm(const FQuantumApiQasmRunRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const
{
    const TSharedRef<FJsonObject> JsonObject = MakeShared<FJsonObject>();
    JsonObject->SetStringField(TEXT("qasm"), Request.Qasm);
    JsonObject->SetStringField(TEXT("qasm_version"), Request.QasmVersion);
    if (Request.bUseAnalyticMode) JsonObject->SetField(TEXT("shots"), MakeShared<FJsonValueNull>());
    else JsonObject->SetNumberField(TEXT("shots"), Request.Shots);
    JsonObject->SetBoolField(TEXT("include_statevector"), Request.bIncludeStatevector);
    if (Request.bSendSeed) JsonObject->SetNumberField(TEXT("seed"), Request.Seed);
    RequestJson(TEXT("/qasm/run"), TEXT("POST"), SerializeJsonObject(JsonObject), Options, false, MoveTemp(OnSuccess), MoveTemp(OnError));
}

void FQuantumApiClient::SubmitCircuitJob(const FQuantumApiCircuitJobRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const
{
    const FString BackendName = ResolveIbmHardwareBackend(Request.BackendName);
    if (BackendName.IsEmpty())
    {
        OnError.ExecuteIfBound(BuildClientError(TEXT("invalid_request"), TEXT("Submit Circuit Job requires a Backend Name or a configured Default IBM Hardware Backend.")));
        return;
    }
    const TSharedRef<FJsonObject> JsonObject = MakeShared<FJsonObject>();
    JsonObject->SetStringField(TEXT("provider"), TEXT("ibm"));
    JsonObject->SetStringField(TEXT("backend_name"), BackendName);
    JsonObject->SetNumberField(TEXT("shots"), Request.Shots);
    SetOptionalString(JsonObject, TEXT("ibm_profile"), ResolveIbmProfile(Request.IbmProfile));
    SetCircuitField(JsonObject, Request.Circuit);
    RequestJson(TEXT("/jobs/circuits"), TEXT("POST"), SerializeJsonObject(JsonObject), Options, false, MoveTemp(OnSuccess), MoveTemp(OnError));
}

void FQuantumApiClient::SubmitQasmJob(const FQuantumApiQasmJobRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const
{
    const FString BackendName = ResolveIbmHardwareBackend(Request.BackendName);
    if (BackendName.IsEmpty())
    {
        OnError.ExecuteIfBound(BuildClientError(TEXT("invalid_request"), TEXT("Submit QASM Job requires a Backend Name or a configured Default IBM Hardware Backend.")));
        return;
    }
    const TSharedRef<FJsonObject> JsonObject = MakeShared<FJsonObject>();
    JsonObject->SetStringField(TEXT("provider"), TEXT("ibm"));
    JsonObject->SetStringField(TEXT("backend_name"), BackendName);
    JsonObject->SetStringField(TEXT("qasm"), Request.Qasm);
    JsonObject->SetStringField(TEXT("qasm_version"), Request.QasmVersion);
    JsonObject->SetNumberField(TEXT("shots"), Request.Shots);
    SetOptionalString(JsonObject, TEXT("ibm_profile"), ResolveIbmProfile(Request.IbmProfile));
    RequestJson(TEXT("/jobs/qasm"), TEXT("POST"), SerializeJsonObject(JsonObject), Options, false, MoveTemp(OnSuccess), MoveTemp(OnError));
}

void FQuantumApiClient::SubmitRandomJob(const FQuantumApiRandomJobRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const
{
    if (Request.Min > Request.Max)
    {
        OnError.ExecuteIfBound(BuildClientError(TEXT("invalid_request"), TEXT("Min must be less than or equal to Max.")));
        return;
    }
    const FString BackendName = ResolveIbmHardwareBackend(Request.BackendName);
    if (BackendName.IsEmpty())
    {
        OnError.ExecuteIfBound(BuildClientError(TEXT("invalid_request"), TEXT("Submit Random Job requires a Backend Name or a configured Default IBM Hardware Backend.")));
        return;
    }
    const TSharedRef<FJsonObject> JsonObject = MakeShared<FJsonObject>();
    JsonObject->SetStringField(TEXT("provider"), TEXT("ibm"));
    JsonObject->SetStringField(TEXT("backend_name"), BackendName);
    JsonObject->SetNumberField(TEXT("min"), Request.Min);
    JsonObject->SetNumberField(TEXT("max"), Request.Max);
    SetOptionalString(JsonObject, TEXT("ibm_profile"), ResolveIbmProfile(Request.IbmProfile));
    RequestJson(TEXT("/jobs/random"), TEXT("POST"), SerializeJsonObject(JsonObject), Options, false, MoveTemp(OnSuccess), MoveTemp(OnError));
}

void FQuantumApiClient::GetJobStatus(const FString& JobId, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const
{
    RequestJson(FString::Printf(TEXT("/jobs/%s"), *FGenericPlatformHttp::UrlEncode(JobId)), TEXT("GET"), TEXT(""), Options, true, MoveTemp(OnSuccess), MoveTemp(OnError));
}

void FQuantumApiClient::GetJobResult(const FString& JobId, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const
{
    RequestJson(FString::Printf(TEXT("/jobs/%s/result"), *FGenericPlatformHttp::UrlEncode(JobId)), TEXT("GET"), TEXT(""), Options, true, MoveTemp(OnSuccess), MoveTemp(OnError));
}

void FQuantumApiClient::CancelJob(const FString& JobId, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const
{
    RequestJson(FString::Printf(TEXT("/jobs/%s/cancel"), *FGenericPlatformHttp::UrlEncode(JobId)), TEXT("POST"), TEXT("{}"), Options, false, MoveTemp(OnSuccess), MoveTemp(OnError));
}

void FQuantumApiClient::CallAdvanced(const FQuantumApiAdvancedRequest& Request, const FQuantumApiRequestOptions& Options, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const
{
    FString Path;
    FString Verb;
    if (!TryGetAdvancedEndpoint(Request.Endpoint, Path, Verb))
    {
        OnError.ExecuteIfBound(BuildClientError(TEXT("unsupported_endpoint"), TEXT("The selected endpoint is not available through the Unreal plugin.")));
        return;
    }
    RequestJson(AppendQuery(Path, Request.QueryParameters), Verb, Request.JsonBody, Options, Verb.Equals(TEXT("GET")), MoveTemp(OnSuccess), MoveTemp(OnError));
}

void FQuantumApiClient::RequestJson(const FString& Path, const FString& Verb, const FString& Body, const FQuantumApiRequestOptions& Options, bool bCanRetry, FQuantumApiJsonDelegate OnSuccess, FQuantumApiErrorDelegate OnError) const
{
    if (IsProtectedPath(Path))
    {
        OnError.ExecuteIfBound(BuildClientError(TEXT("protected_endpoint"), TEXT("Credential lifecycle and metrics routes are intentionally not exposed by this runtime plugin.")));
        return;
    }
    if (BaseUrl.IsEmpty())
    {
        OnError.ExecuteIfBound(BuildClientError(TEXT("configuration_error"), TEXT("Backend Proxy mode requires a Backend Proxy URL.")));
        return;
    }
    const FString ApiKey = !Options.OverrideApiKey.IsEmpty() ? Options.OverrideApiKey : DefaultApiKey;
    if (AuthMode == EQuantumApiAuthMode::DirectApiKey && ApiKey.IsEmpty())
    {
        OnError.ExecuteIfBound(BuildClientError(TEXT("configuration_error"), TEXT("Direct API Key mode requires an API Key.")));
        return;
    }

    const TSharedRef<FQuantumApiPendingRequest, ESPMode::ThreadSafe> Pending = MakeShared<FQuantumApiPendingRequest, ESPMode::ThreadSafe>();
    Pending->Path = Path;
    Pending->Verb = Verb;
    Pending->Body = Body;
    Pending->Options = Options;
    Pending->bCanRetry = bCanRetry && Verb.Equals(TEXT("GET"), ESearchCase::IgnoreCase);
    Pending->OnSuccess = MoveTemp(OnSuccess);
    Pending->OnError = MoveTemp(OnError);
    DispatchRequest(Pending);
}

bool FQuantumApiClient::TryGetAdvancedEndpoint(EQuantumApiAdvancedEndpoint Endpoint, FString& OutPath, FString& OutVerb)
{
    switch (Endpoint)
    {
    case EQuantumApiAdvancedEndpoint::PortfolioMetadata: OutPath = TEXT("/portfolio.json"); OutVerb = TEXT("GET"); return true;
    case EQuantumApiAdvancedEndpoint::GroverSearch: OutPath = TEXT("/algorithms/grover_search"); break;
    case EQuantumApiAdvancedEndpoint::AmplitudeEstimation: OutPath = TEXT("/algorithms/amplitude_estimation"); break;
    case EQuantumApiAdvancedEndpoint::PhaseEstimation: OutPath = TEXT("/algorithms/phase_estimation"); break;
    case EQuantumApiAdvancedEndpoint::TimeEvolution: OutPath = TEXT("/algorithms/time_evolution"); break;
    case EQuantumApiAdvancedEndpoint::Qaoa: OutPath = TEXT("/optimization/qaoa"); break;
    case EQuantumApiAdvancedEndpoint::Vqe: OutPath = TEXT("/optimization/vqe"); break;
    case EQuantumApiAdvancedEndpoint::Maxcut: OutPath = TEXT("/optimization/maxcut"); break;
    case EQuantumApiAdvancedEndpoint::Knapsack: OutPath = TEXT("/optimization/knapsack"); break;
    case EQuantumApiAdvancedEndpoint::TravelingSalesperson: OutPath = TEXT("/optimization/tsp"); break;
    case EQuantumApiAdvancedEndpoint::StateTomography: OutPath = TEXT("/experiments/state_tomography"); break;
    case EQuantumApiAdvancedEndpoint::RandomizedBenchmarking: OutPath = TEXT("/experiments/randomized_benchmarking"); break;
    case EQuantumApiAdvancedEndpoint::QuantumVolume: OutPath = TEXT("/experiments/quantum_volume"); break;
    case EQuantumApiAdvancedEndpoint::T1: OutPath = TEXT("/experiments/t1"); break;
    case EQuantumApiAdvancedEndpoint::T2Ramsey: OutPath = TEXT("/experiments/t2ramsey"); break;
    case EQuantumApiAdvancedEndpoint::PortfolioOptimization: OutPath = TEXT("/finance/portfolio_optimization"); break;
    case EQuantumApiAdvancedEndpoint::PortfolioDiversification: OutPath = TEXT("/finance/portfolio_diversification"); break;
    case EQuantumApiAdvancedEndpoint::KernelClassifier: OutPath = TEXT("/ml/kernel_classifier"); break;
    case EQuantumApiAdvancedEndpoint::VqcClassifier: OutPath = TEXT("/ml/vqc_classifier"); break;
    case EQuantumApiAdvancedEndpoint::QsvrRegressor: OutPath = TEXT("/ml/qsvr_regressor"); break;
    case EQuantumApiAdvancedEndpoint::GroundStateEnergy: OutPath = TEXT("/nature/ground_state_energy"); break;
    case EQuantumApiAdvancedEndpoint::FermionicMappingPreview: OutPath = TEXT("/nature/fermionic_mapping_preview"); break;
    default: return false;
    }
    OutVerb = TEXT("POST");
    return true;
}

bool FQuantumApiClient::ShouldRetryRequest(const FString& Verb, int32 StatusCode, int32 Attempt, int32 InMaxReadRetries)
{
    if (!Verb.Equals(TEXT("GET"), ESearchCase::IgnoreCase) || Attempt >= InMaxReadRetries)
    {
        return false;
    }
    return StatusCode == 0 || StatusCode == 429 || StatusCode == 502 || StatusCode == 503 || StatusCode == 504;
}

FQuantumApiTransportRequest FQuantumApiClient::BuildTransportRequest(const FString& Path, const FString& Verb, const FString& Body, const FQuantumApiRequestOptions& Options) const
{
    FQuantumApiTransportRequest Request;
    Request.Url = BaseUrl + Path;
    Request.Verb = Verb;
    Request.Body = Body;
    Request.TimeoutSeconds = RequestTimeoutSeconds;
    Request.Headers.Add(TEXT("Accept"), TEXT("application/json"));
    Request.Headers.Add(TEXT("Content-Type"), TEXT("application/json"));

    const FString ApiKey = !Options.OverrideApiKey.IsEmpty() ? Options.OverrideApiKey : DefaultApiKey;
    if (!ApiKey.IsEmpty() && AuthMode == EQuantumApiAuthMode::DirectApiKey)
    {
        Request.Headers.Add(TEXT("X-API-Key"), ApiKey);
    }
    for (const TPair<FString, FString>& Header : Options.ExtraHeaders)
    {
        Request.Headers.Add(Header.Key, Header.Value);
    }
    return Request;
}

void FQuantumApiClient::DispatchRequest(const TSharedRef<FQuantumApiPendingRequest, ESPMode::ThreadSafe>& Pending) const
{
    Transport->Send(BuildTransportRequest(Pending->Path, Pending->Verb, Pending->Body, Pending->Options), FQuantumApiTransportCompletion::CreateLambda([this, Pending](const FQuantumApiTransportResponse& Response)
    {
        const int32 StatusCode = Response.StatusCode;
        if ((!Response.bConnectedSuccessfully || !EHttpResponseCodes::IsOk(StatusCode)) && Pending->bCanRetry && ShouldRetryRequest(Pending->Verb, StatusCode, Pending->Attempt, MaxReadRetries))
        {
            ++Pending->Attempt;
            float Delay = Pending->Attempt == 1 ? 0.25f : 1.0f;
            if (const FString* RetryAfter = FindHeaderValue(Response.Headers, TEXT("Retry-After")))
            {
                if (!RetryAfter->IsEmpty()) Delay = FMath::Clamp(FCString::Atof(**RetryAfter), 0.0f, MaxRetryDelaySeconds);
            }
            FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([this, Pending](float)
            {
                DispatchRequest(Pending);
                return false;
            }), FMath::Min(Delay, MaxRetryDelaySeconds));
            return;
        }

        if (!Response.bConnectedSuccessfully)
        {
            Pending->OnError.ExecuteIfBound(BuildTransportError(TEXT("Network request failed.")));
            return;
        }
        if (!EHttpResponseCodes::IsOk(StatusCode))
        {
            Pending->OnError.ExecuteIfBound(BuildResponseError(Response));
            return;
        }
        FQuantumApiJsonResponse Payload;
        Payload.Json = Response.Body;
        Payload.Meta = BuildResponseMeta(Response);
        Pending->OnSuccess.ExecuteIfBound(Payload);
    }));
}

FQuantumApiError FQuantumApiClient::BuildClientError(const FString& ErrorCode, const FString& Message)
{
    FQuantumApiError Error;
    Error.Error = ErrorCode;
    Error.Message = Message;
    return Error;
}

FQuantumApiError FQuantumApiClient::BuildTransportError(const FString& Message)
{
    return BuildClientError(TEXT("transport_error"), Message);
}

FQuantumApiError FQuantumApiClient::BuildResponseError(const FQuantumApiTransportResponse& Response)
{
    FQuantumApiError Error;
    Error.StatusCode = Response.StatusCode;
    Error.Headers = Response.Headers;
    Error.RawBody = Response.Body;
    if (const FString* RequestId = FindHeaderValue(Response.Headers, TEXT("X-Request-ID"))) Error.RequestId = *RequestId;
    Error.bRetryable = Error.StatusCode == 429 || Error.StatusCode == 502 || Error.StatusCode == 503 || Error.StatusCode == 504;
    if (const FString* RetryAfter = FindHeaderValue(Response.Headers, TEXT("Retry-After"))) Error.RetryAfterSeconds = FCString::Atof(**RetryAfter);
    TSharedPtr<FJsonObject> JsonObject;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Error.RawBody);
    if (FJsonSerializer::Deserialize(Reader, JsonObject) && JsonObject.IsValid())
    {
        JsonObject->TryGetStringField(TEXT("error"), Error.Error);
        JsonObject->TryGetStringField(TEXT("message"), Error.Message);
        JsonObject->TryGetStringField(TEXT("request_id"), Error.RequestId);
        if (Error.Message.IsEmpty()) JsonObject->TryGetStringField(TEXT("detail"), Error.Message);
    }
    if (Error.Error.IsEmpty()) Error.Error = TEXT("http_error");
    if (Error.Message.IsEmpty()) Error.Message = TEXT("Quantum API request failed.");
    return Error;
}

FQuantumApiResponseMeta FQuantumApiClient::BuildResponseMeta(const FQuantumApiTransportResponse& Response)
{
    FQuantumApiResponseMeta Meta;
    Meta.StatusCode = Response.StatusCode;
    Meta.Headers = Response.Headers;
    if (const FString* RequestId = FindHeaderValue(Response.Headers, TEXT("X-Request-ID"))) Meta.RequestId = *RequestId;
    return Meta;
}

FString FQuantumApiClient::SerializeJsonObject(const TSharedRef<FJsonObject>& JsonObject)
{
    FString Body;
    const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Body);
    FJsonSerializer::Serialize(JsonObject, Writer);
    return Body;
}

TSharedRef<FJsonObject> FQuantumApiClient::SerializeCircuit(const FQuantumApiCircuitDefinition& Circuit)
{
    const TSharedRef<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetNumberField(TEXT("num_qubits"), Circuit.NumQubits);
    TArray<TSharedPtr<FJsonValue>> Operations;
    for (const FQuantumApiCircuitOperation& Operation : Circuit.Operations)
    {
        const TSharedRef<FJsonObject> Item = MakeShared<FJsonObject>();
        Item->SetStringField(TEXT("gate"), Operation.Gate);
        Item->SetNumberField(TEXT("target"), Operation.Target);
        if (Operation.bSendTheta) Item->SetNumberField(TEXT("theta"), Operation.Theta);
        if (Operation.bSendControl) Item->SetNumberField(TEXT("control"), Operation.Control);
        Operations.Add(MakeShared<FJsonValueObject>(Item));
    }
    Result->SetArrayField(TEXT("operations"), Operations);
    return Result;
}

FString FQuantumApiClient::AppendQuery(const FString& Path, const TMap<FString, FString>& QueryParameters)
{
    if (QueryParameters.IsEmpty()) return Path;
    FString Result = Path + TEXT("?");
    bool bFirst = true;
    for (const TPair<FString, FString>& Pair : QueryParameters)
    {
        if (!bFirst) Result += TEXT("&");
        Result += FGenericPlatformHttp::UrlEncode(Pair.Key) + TEXT("=") + FGenericPlatformHttp::UrlEncode(Pair.Value);
        bFirst = false;
    }
    return Result;
}

FString FQuantumApiClient::ResolveIbmProfile(const FString& RequestProfile) const
{
    FString Profile = RequestProfile;
    Profile.TrimStartAndEndInline();
    return Profile.IsEmpty() ? DefaultIbmProfile : Profile;
}

FString FQuantumApiClient::ResolveIbmHardwareBackend(const FString& RequestBackendName) const
{
    FString BackendName = RequestBackendName;
    BackendName.TrimStartAndEndInline();
    return BackendName.IsEmpty() ? DefaultIbmHardwareBackend : BackendName;
}

bool FQuantumApiClient::ShouldUseDefaultIbmProfile(const FString& Provider, const FString& BackendName, bool bAssumeIbmProviderIfMissing)
{
    FString NormalizedProvider = Provider;
    NormalizedProvider.TrimStartAndEndInline();
    NormalizedProvider.ToLowerInline();
    if (NormalizedProvider == TEXT("ibm"))
    {
        return true;
    }

    FString NormalizedBackendName = BackendName;
    NormalizedBackendName.TrimStartAndEndInline();
    NormalizedBackendName.ToLowerInline();
    return NormalizedProvider.IsEmpty() && (bAssumeIbmProviderIfMissing || NormalizedBackendName.StartsWith(TEXT("ibm")));
}

bool FQuantumApiClient::IsProtectedPath(const FString& Path)
{
    return Path.StartsWith(TEXT("/keys"))
        || Path.StartsWith(TEXT("/v1/keys"))
        || Path.StartsWith(TEXT("/ibm/profiles"))
        || Path.StartsWith(TEXT("/v1/ibm/profiles"))
        || Path.StartsWith(TEXT("/metrics"))
        || Path.StartsWith(TEXT("/v1/metrics"));
}
