// Copyright (c) 2026 David J. Grimsley. All rights reserved.
#if WITH_DEV_AUTOMATION_TESTS

#include "Dom/JsonObject.h"
#include "Misc/AutomationTest.h"
#include "QuantumApiClient.h"
#include "QuantumApiSettings.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace
{
class FQuantumApiMockTransport final : public IQuantumApiTransport
{
public:
    TArray<FQuantumApiTransportRequest> Requests;
    TArray<FQuantumApiTransportResponse> QueuedResponses;

    virtual void Send(const FQuantumApiTransportRequest& Request, FQuantumApiTransportCompletion Completion) override
    {
        Requests.Add(Request);
        FQuantumApiTransportResponse Response;
        if (!QueuedResponses.IsEmpty())
        {
            Response = QueuedResponses[0];
            QueuedResponses.RemoveAt(0);
        }
        Completion.ExecuteIfBound(Response);
    }
};

UQuantumApiSettings* MakeSettings(EQuantumApiAuthMode AuthMode)
{
    UQuantumApiSettings* Settings = NewObject<UQuantumApiSettings>();
    Settings->AuthMode = AuthMode;
    Settings->ApiKey = TEXT("unit-test-key");
    Settings->BackendProxyUrl = TEXT("https://proxy.example.test/quantum");
    Settings->DefaultIbmProfile = TEXT("IBM Open");
    Settings->DefaultIbmHardwareBackend = TEXT("ibm_default");
    Settings->MaxReadRetries = 2;
    return Settings;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FQuantumApiTransportSpec,
    "QuantumApi.Runtime.Transport",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter
)

bool FQuantumApiTransportSpec::RunTest(const FString& Parameters)
{
    UQuantumApiSettings* DirectUrlSettings = MakeSettings(EQuantumApiAuthMode::DirectApiKey);
    TestEqual(TEXT("Direct mode always uses the hosted Quantum API URL"), DirectUrlSettings->GetResolvedBaseUrl(), FString(TEXT("https://davidjgrimsley.com/public-facing/api/quantum/v1")));
    UQuantumApiSettings* ProxyUrlSettings = MakeSettings(EQuantumApiAuthMode::BackendProxy);
    ProxyUrlSettings->BackendProxyUrl = TEXT(" https://proxy.example.test/quantum/ ");
    TestEqual(TEXT("Proxy URL is normalized to the mounted v1 contract"), ProxyUrlSettings->GetResolvedBaseUrl(), FString(TEXT("https://proxy.example.test/quantum/v1")));

    const TSharedRef<FQuantumApiMockTransport> Mock = MakeShared<FQuantumApiMockTransport>();
    FQuantumApiTransportResponse GateResponse;
    GateResponse.bConnectedSuccessfully = true;
    GateResponse.StatusCode = 200;
    GateResponse.Body = TEXT("{\"gate_type\":\"rotation\",\"measurement\":1,\"success\":true}");
    GateResponse.Headers.Add(TEXT("X-Request-ID"), TEXT("request-gate-1"));
    Mock->QueuedResponses.Add(GateResponse);

    FQuantumApiClient Client(MakeSettings(EQuantumApiAuthMode::DirectApiKey), Mock);
    FQuantumApiRunGateRequest GateRequest;
    GateRequest.GateType = TEXT("rotation");
    GateRequest.bSendRotationAngle = true;
    GateRequest.RotationAngleRad = PI / 2.0;

    bool bGateSucceeded = false;
    FQuantumApiRunGateResponse GatePayload;
    Client.RunGate(GateRequest, FQuantumApiRequestOptions(),
        FQuantumApiRunGateDelegate::CreateLambda([&bGateSucceeded, &GatePayload](const FQuantumApiRunGateResponse& Response)
        {
            bGateSucceeded = true;
            GatePayload = Response;
        }),
        FQuantumApiErrorDelegate::CreateLambda([this](const FQuantumApiError& Error)
        {
            AddError(FString::Printf(TEXT("Unexpected gate error: %s"), *Error.Message));
        }));

    TestTrue(TEXT("Gate response is parsed"), bGateSucceeded);
    TestEqual(TEXT("Gate request count"), Mock->Requests.Num(), 1);
    TestEqual(TEXT("Gate URL uses the hosted API"), Mock->Requests[0].Url, FString(TEXT("https://davidjgrimsley.com/public-facing/api/quantum/v1/gates/run")));
    TestEqual(TEXT("Gate verb"), Mock->Requests[0].Verb, FString(TEXT("POST")));
    TestEqual(TEXT("Direct API key header"), Mock->Requests[0].Headers.FindRef(TEXT("X-API-Key")), FString(TEXT("unit-test-key")));
    TestFalse(TEXT("Plugin does not generate a bearer authorization header"), Mock->Requests[0].Headers.Contains(TEXT("Authorization")));
    TestTrue(TEXT("Rotation angle is serialized"), Mock->Requests[0].Body.Contains(TEXT("rotation_angle_rad")));
    TestEqual(TEXT("Success request ID is preserved"), GatePayload.Meta.RequestId, FString(TEXT("request-gate-1")));

    const TSharedRef<FQuantumApiMockTransport> ProxyMock = MakeShared<FQuantumApiMockTransport>();
    FQuantumApiTransportResponse ProxyResponse;
    ProxyResponse.bConnectedSuccessfully = true;
    ProxyResponse.StatusCode = 200;
    ProxyResponse.Body = TEXT("{\"status\":\"ok\"}");
    ProxyMock->QueuedResponses.Add(ProxyResponse);
    FQuantumApiClient ProxyClient(MakeSettings(EQuantumApiAuthMode::BackendProxy), ProxyMock);
    ProxyClient.HealthCheck(FQuantumApiRequestOptions(), FQuantumApiHealthDelegate(), FQuantumApiErrorDelegate());
    TestFalse(TEXT("Proxy mode omits direct API key"), ProxyMock->Requests[0].Headers.Contains(TEXT("X-API-Key")));
    TestEqual(TEXT("Proxy mode uses the configured proxy URL"), ProxyMock->Requests[0].Url, FString(TEXT("https://proxy.example.test/quantum/v1/health")));

    const TSharedRef<FQuantumApiMockTransport> MissingDirectKeyMock = MakeShared<FQuantumApiMockTransport>();
    UQuantumApiSettings* MissingDirectKeySettings = MakeSettings(EQuantumApiAuthMode::DirectApiKey);
    MissingDirectKeySettings->ApiKey.Empty();
    FQuantumApiClient MissingDirectKeyClient(MissingDirectKeySettings, MissingDirectKeyMock);
    FQuantumApiError MissingDirectKeyError;
    MissingDirectKeyClient.HealthCheck(FQuantumApiRequestOptions(), FQuantumApiHealthDelegate(), FQuantumApiErrorDelegate::CreateLambda([&MissingDirectKeyError](const FQuantumApiError& Error) { MissingDirectKeyError = Error; }));
    TestEqual(TEXT("Missing direct key is a configuration error"), MissingDirectKeyError.Error, FString(TEXT("configuration_error")));
    TestEqual(TEXT("Missing direct key makes no request"), MissingDirectKeyMock->Requests.Num(), 0);

    const TSharedRef<FQuantumApiMockTransport> MissingProxyUrlMock = MakeShared<FQuantumApiMockTransport>();
    UQuantumApiSettings* MissingProxyUrlSettings = MakeSettings(EQuantumApiAuthMode::BackendProxy);
    MissingProxyUrlSettings->BackendProxyUrl.Empty();
    FQuantumApiClient MissingProxyUrlClient(MissingProxyUrlSettings, MissingProxyUrlMock);
    FQuantumApiError MissingProxyUrlError;
    MissingProxyUrlClient.HealthCheck(FQuantumApiRequestOptions(), FQuantumApiHealthDelegate(), FQuantumApiErrorDelegate::CreateLambda([&MissingProxyUrlError](const FQuantumApiError& Error) { MissingProxyUrlError = Error; }));
    TestEqual(TEXT("Missing proxy URL is a configuration error"), MissingProxyUrlError.Error, FString(TEXT("configuration_error")));
    TestEqual(TEXT("Missing proxy URL makes no request"), MissingProxyUrlMock->Requests.Num(), 0);

    const TSharedRef<FQuantumApiMockTransport> ErrorMock = MakeShared<FQuantumApiMockTransport>();
    FQuantumApiTransportResponse ErrorResponse;
    ErrorResponse.bConnectedSuccessfully = true;
    ErrorResponse.StatusCode = 400;
    ErrorResponse.Body = TEXT("{\"error\":\"validation_error\",\"message\":\"min must not exceed max\",\"request_id\":\"request-error-1\"}");
    ErrorMock->QueuedResponses.Add(ErrorResponse);
    FQuantumApiClient ErrorClient(MakeSettings(EQuantumApiAuthMode::DirectApiKey), ErrorMock);
    FQuantumApiError ReceivedError;
    ErrorClient.RunGate(GateRequest, FQuantumApiRequestOptions(), FQuantumApiRunGateDelegate(),
        FQuantumApiErrorDelegate::CreateLambda([&ReceivedError](const FQuantumApiError& Error) { ReceivedError = Error; }));
    TestEqual(TEXT("HTTP error code is preserved"), ReceivedError.Error, FString(TEXT("validation_error")));
    TestEqual(TEXT("Error request ID is preserved"), ReceivedError.RequestId, FString(TEXT("request-error-1")));

    TestTrue(TEXT("GET 429 is retryable"), FQuantumApiClient::ShouldRetryRequest(TEXT("GET"), 429, 0, 2));
    TestFalse(TEXT("POST random is never retryable"), FQuantumApiClient::ShouldRetryRequest(TEXT("POST"), 503, 0, 2));
    TestFalse(TEXT("Retry budget is bounded"), FQuantumApiClient::ShouldRetryRequest(TEXT("GET"), 503, 2, 2));

    const TSharedRef<FQuantumApiMockTransport> PostMock = MakeShared<FQuantumApiMockTransport>();
    FQuantumApiTransportResponse UnavailableResponse;
    UnavailableResponse.bConnectedSuccessfully = true;
    UnavailableResponse.StatusCode = 503;
    PostMock->QueuedResponses.Add(UnavailableResponse);
    FQuantumApiClient PostClient(MakeSettings(EQuantumApiAuthMode::DirectApiKey), PostMock);
    PostClient.GenerateRandomInt(FQuantumApiRandomIntRequest(), FQuantumApiRequestOptions(), FQuantumApiRandomIntDelegate(), FQuantumApiErrorDelegate());
    TestEqual(TEXT("POST random is dispatched exactly once"), PostMock->Requests.Num(), 1);

    const TSharedRef<FQuantumApiMockTransport> BoundsMock = MakeShared<FQuantumApiMockTransport>();
    FQuantumApiRandomIntRequest InvalidBounds;
    InvalidBounds.Min = 2;
    InvalidBounds.Max = 1;
    FQuantumApiClient BoundsClient(MakeSettings(EQuantumApiAuthMode::DirectApiKey), BoundsMock);
    BoundsClient.GenerateRandomInt(InvalidBounds, FQuantumApiRequestOptions(), FQuantumApiRandomIntDelegate(), FQuantumApiErrorDelegate());
    TestEqual(TEXT("Invalid QRNG bounds do not make a request"), BoundsMock->Requests.Num(), 0);

    const TSharedRef<FQuantumApiMockTransport> BackendMock = MakeShared<FQuantumApiMockTransport>();
    FQuantumApiClient BackendClient(MakeSettings(EQuantumApiAuthMode::DirectApiKey), BackendMock);
    FQuantumApiBackendListRequest BackendRequest;
    BackendRequest.Provider = TEXT("ibm");
    BackendClient.ListBackends(BackendRequest, FQuantumApiRequestOptions(), FQuantumApiJsonDelegate(), FQuantumApiErrorDelegate());
    TestTrue(TEXT("IBM backend list uses configured profile fallback"), BackendMock->Requests[0].Url.Contains(TEXT("ibm_profile=IBM%20Open")));

    const TSharedRef<FQuantumApiMockTransport> HardwareMock = MakeShared<FQuantumApiMockTransport>();
    FQuantumApiClient HardwareClient(MakeSettings(EQuantumApiAuthMode::DirectApiKey), HardwareMock);
    FQuantumApiRandomJobRequest HardwareRequest;
    HardwareClient.SubmitRandomJob(HardwareRequest, FQuantumApiRequestOptions(), FQuantumApiJsonDelegate(), FQuantumApiErrorDelegate());
    TestTrue(TEXT("IBM random job uses configured profile fallback"), HardwareMock->Requests[0].Body.Contains(TEXT("\"ibm_profile\"")) && HardwareMock->Requests[0].Body.Contains(TEXT("IBM Open")));
    TestTrue(TEXT("IBM random job uses configured backend fallback"), HardwareMock->Requests[0].Body.Contains(TEXT("\"backend_name\"")) && HardwareMock->Requests[0].Body.Contains(TEXT("ibm_default")));

    const TSharedRef<FQuantumApiMockTransport> HardwareOverrideMock = MakeShared<FQuantumApiMockTransport>();
    FQuantumApiClient HardwareOverrideClient(MakeSettings(EQuantumApiAuthMode::DirectApiKey), HardwareOverrideMock);
    FQuantumApiRandomJobRequest HardwareOverrideRequest;
    HardwareOverrideRequest.BackendName = TEXT("ibm_node_override");
    HardwareOverrideClient.SubmitRandomJob(HardwareOverrideRequest, FQuantumApiRequestOptions(), FQuantumApiJsonDelegate(), FQuantumApiErrorDelegate());
    TestTrue(TEXT("IBM node backend overrides configured default"), HardwareOverrideMock->Requests[0].Body.Contains(TEXT("\"backend_name\"")) && HardwareOverrideMock->Requests[0].Body.Contains(TEXT("ibm_node_override")));

    const TSharedRef<FQuantumApiMockTransport> TranspileDefaultMock = MakeShared<FQuantumApiMockTransport>();
    FQuantumApiClient TranspileDefaultClient(MakeSettings(EQuantumApiAuthMode::DirectApiKey), TranspileDefaultMock);
    FQuantumApiTranspileRequest TranspileDefaultRequest;
    TranspileDefaultClient.Transpile(TranspileDefaultRequest, FQuantumApiRequestOptions(), FQuantumApiJsonDelegate(), FQuantumApiErrorDelegate());
    TestTrue(TEXT("Transpile uses configured IBM backend fallback"), TranspileDefaultMock->Requests[0].Body.Contains(TEXT("\"backend_name\"")) && TranspileDefaultMock->Requests[0].Body.Contains(TEXT("ibm_default")));

    const TSharedRef<FQuantumApiMockTransport> MissingHardwareBackendMock = MakeShared<FQuantumApiMockTransport>();
    UQuantumApiSettings* MissingHardwareBackendSettings = MakeSettings(EQuantumApiAuthMode::DirectApiKey);
    MissingHardwareBackendSettings->DefaultIbmHardwareBackend.Empty();
    FQuantumApiClient MissingHardwareBackendClient(MissingHardwareBackendSettings, MissingHardwareBackendMock);
    FQuantumApiError MissingHardwareBackendError;
    MissingHardwareBackendClient.SubmitRandomJob(FQuantumApiRandomJobRequest(), FQuantumApiRequestOptions(), FQuantumApiJsonDelegate(), FQuantumApiErrorDelegate::CreateLambda([&MissingHardwareBackendError](const FQuantumApiError& Error) { MissingHardwareBackendError = Error; }));
    TestEqual(TEXT("Missing IBM backend is rejected locally"), MissingHardwareBackendError.Error, FString(TEXT("invalid_request")));
    TestEqual(TEXT("Missing IBM backend makes no request"), MissingHardwareBackendMock->Requests.Num(), 0);

    const TSharedRef<FQuantumApiMockTransport> BraidMock = MakeShared<FQuantumApiMockTransport>();
    FQuantumApiTransportResponse BraidResponse;
    BraidResponse.bConnectedSuccessfully = true;
    BraidResponse.StatusCode = 200;
    BraidResponse.Headers.Add(TEXT("X-Request-ID"), TEXT("request-braid-1"));
    BraidResponse.Body = TEXT("{\"model\":\"fibonacci\",\"anyon_count\":3,\"total_charge\":\"tau\",\"initial_state\":\"0\",\"braid_word\":[{\"generator\":1,\"power\":-1}],\"logical_state\":[{\"real\":0.6,\"imag\":0.2},{\"real\":0.714142842854285,\"imag\":-0.3}],\"fusion_probabilities\":{\"vacuum\":0.4,\"tau\":0.6},\"measurement\":\"tau\",\"shots\":2,\"counts\":{\"vacuum\":0,\"tau\":2},\"metadata\":{\"simulation_type\":\"digital_simulation_of_fibonacci_braid\",\"convention\":\"test\",\"logical_dimension\":2}}");
    BraidMock->QueuedResponses.Add(BraidResponse);
    FQuantumApiClient BraidClient(MakeSettings(EQuantumApiAuthMode::DirectApiKey), BraidMock);
    FQuantumApiTopologicalBraidRequest BraidRequest;
    FQuantumApiBraidOperation BraidOperation;
    BraidOperation.Power = -1;
    BraidRequest.BraidWord.Add(BraidOperation);
    FQuantumApiTopologicalBraidResponse BraidPayload;
    BraidClient.EvaluateTopologicalBraidTyped(BraidRequest, FQuantumApiRequestOptions(),
        FQuantumApiTopologicalBraidDelegate::CreateLambda([&BraidPayload](const FQuantumApiTopologicalBraidResponse& Response) { BraidPayload = Response; }),
        FQuantumApiErrorDelegate::CreateLambda([this](const FQuantumApiError& Error) { AddError(FString::Printf(TEXT("Unexpected braid error: %s"), *Error.Message)); }));
    TestEqual(TEXT("Typed braid uses the braid route"), BraidMock->Requests[0].Url, FString(TEXT("https://davidjgrimsley.com/public-facing/api/quantum/v1/topological/braid")));
    TestEqual(TEXT("Typed braid keeps complex state length"), BraidPayload.LogicalState.Num(), 2);
    if (BraidPayload.LogicalState.Num() != 2) return false;
    TestEqual(TEXT("Typed braid keeps imaginary phase"), BraidPayload.LogicalState[1].Imag, -0.3);
    TestEqual(TEXT("Typed braid exposes tau probability"), BraidPayload.TauProbability, 0.6);
    TestEqual(TEXT("Typed braid exposes measurement"), BraidPayload.Measurement, FString(TEXT("tau")));
    TestEqual(TEXT("Typed braid exposes counts"), BraidPayload.Counts.FindRef(TEXT("tau")), 2);
    TestEqual(TEXT("Typed braid keeps request ID"), BraidPayload.Meta.RequestId, FString(TEXT("request-braid-1")));

    const TSharedRef<FQuantumApiMockTransport> EvolutionMock = MakeShared<FQuantumApiMockTransport>();
    FQuantumApiTransportResponse EvolutionResponse;
    EvolutionResponse.bConnectedSuccessfully = true;
    EvolutionResponse.StatusCode = 200;
    EvolutionResponse.Body = TEXT("{\"final_statevector\":[{\"real\":0.5,\"imag\":-0.5},{\"real\":0.5,\"imag\":0.5}],\"final_probabilities\":[0.5,0.5],\"variant\":\"trotter_qrte\",\"provider\":\"qiskit-algorithms\",\"backend_mode\":\"statevector_estimator\"}");
    EvolutionMock->QueuedResponses.Add(EvolutionResponse);
    FQuantumApiClient EvolutionClient(MakeSettings(EQuantumApiAuthMode::DirectApiKey), EvolutionMock);
    FQuantumApiTimeEvolutionRequest EvolutionRequest;
    EvolutionRequest.InitialStatevector = BraidPayload.LogicalState;
    FQuantumApiPauliTerm XTerm;
    XTerm.Pauli = TEXT("X");
    XTerm.Coefficient = 0.25;
    EvolutionRequest.Hamiltonian.Add(XTerm);
    FQuantumApiPauliTerm ZTerm;
    ZTerm.Pauli = TEXT("Z");
    ZTerm.Coefficient = 0.75;
    EvolutionRequest.Hamiltonian.Add(ZTerm);
    FQuantumApiTimeEvolutionResponse EvolutionPayload;
    EvolutionClient.RunTimeEvolution(EvolutionRequest, FQuantumApiRequestOptions(),
        FQuantumApiTimeEvolutionDelegate::CreateLambda([&EvolutionPayload](const FQuantumApiTimeEvolutionResponse& Response) { EvolutionPayload = Response; }),
        FQuantumApiErrorDelegate::CreateLambda([this](const FQuantumApiError& Error) { AddError(FString::Printf(TEXT("Unexpected evolution error: %s"), *Error.Message)); }));
    TestEqual(TEXT("Evolution uses the algorithm route"), EvolutionMock->Requests[0].Url, FString(TEXT("https://davidjgrimsley.com/public-facing/api/quantum/v1/algorithms/time_evolution")));
    TSharedPtr<FJsonObject> EvolutionBody;
    TestTrue(TEXT("Evolution request is JSON"), FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(EvolutionMock->Requests[0].Body), EvolutionBody) && EvolutionBody.IsValid());
    if (!EvolutionBody.IsValid()) return false;
    const TArray<TSharedPtr<FJsonValue>>* SentState = nullptr;
    TestTrue(TEXT("Evolution sends complex statevector"), EvolutionBody->TryGetArrayField(TEXT("initial_statevector"), SentState) && SentState != nullptr && SentState->Num() == 2);
    if (SentState == nullptr || SentState->Num() != 2) return false;
    double SentImag = 0.0;
    TestTrue(TEXT("Evolution preserves imaginary phase"), (*SentState)[1]->AsObject()->TryGetNumberField(TEXT("imag"), SentImag) && FMath::IsNearlyEqual(SentImag, -0.3, 1e-9));
    TestFalse(TEXT("Evolution does not send a circuit"), EvolutionBody->HasField(TEXT("initial_state")));
    if (EvolutionPayload.FinalStatevector.Num() != 2 || EvolutionPayload.FinalProbabilities.Num() != 2) return false;
    TestEqual(TEXT("Evolution parses final phase"), EvolutionPayload.FinalStatevector[0].Imag, -0.5);
    TestEqual(TEXT("Evolution parses aligned probabilities"), EvolutionPayload.FinalProbabilities[1], 0.5);

    const TSharedRef<FQuantumApiMockTransport> InvalidEvolutionMock = MakeShared<FQuantumApiMockTransport>();
    FQuantumApiClient InvalidEvolutionClient(MakeSettings(EQuantumApiAuthMode::DirectApiKey), InvalidEvolutionMock);
    FQuantumApiError InvalidEvolutionError;
    InvalidEvolutionClient.RunTimeEvolution(FQuantumApiTimeEvolutionRequest(), FQuantumApiRequestOptions(), FQuantumApiTimeEvolutionDelegate(),
        FQuantumApiErrorDelegate::CreateLambda([&InvalidEvolutionError](const FQuantumApiError& Error) { InvalidEvolutionError = Error; }));
    TestEqual(TEXT("Missing evolution state is rejected locally"), InvalidEvolutionError.Error, FString(TEXT("invalid_request")));
    TestEqual(TEXT("Invalid evolution makes no request"), InvalidEvolutionMock->Requests.Num(), 0);
    FQuantumApiTimeEvolutionRequest NonUnitEvolutionRequest = EvolutionRequest;
    NonUnitEvolutionRequest.InitialStatevector[0].Real = 0.0;
    FQuantumApiError NonUnitEvolutionError;
    InvalidEvolutionClient.RunTimeEvolution(NonUnitEvolutionRequest, FQuantumApiRequestOptions(), FQuantumApiTimeEvolutionDelegate(),
        FQuantumApiErrorDelegate::CreateLambda([&NonUnitEvolutionError](const FQuantumApiError& Error) { NonUnitEvolutionError = Error; }));
    TestEqual(TEXT("Non-unit evolution state is rejected locally"), NonUnitEvolutionError.Error, FString(TEXT("invalid_request")));
    TestEqual(TEXT("Non-unit evolution makes no request"), InvalidEvolutionMock->Requests.Num(), 0);

    const TSharedRef<FQuantumApiMockTransport> MalformedEvolutionMock = MakeShared<FQuantumApiMockTransport>();
    EvolutionResponse.Body = TEXT("{\"final_statevector\":[{\"real\":1,\"imag\":0}],\"variant\":\"trotter_qrte\",\"provider\":\"qiskit-algorithms\",\"backend_mode\":\"statevector_estimator\"}");
    MalformedEvolutionMock->QueuedResponses.Add(EvolutionResponse);
    FQuantumApiClient MalformedEvolutionClient(MakeSettings(EQuantumApiAuthMode::DirectApiKey), MalformedEvolutionMock);
    FQuantumApiError MalformedEvolutionError;
    MalformedEvolutionClient.RunTimeEvolution(EvolutionRequest, FQuantumApiRequestOptions(), FQuantumApiTimeEvolutionDelegate(),
        FQuantumApiErrorDelegate::CreateLambda([&MalformedEvolutionError](const FQuantumApiError& Error) { MalformedEvolutionError = Error; }));
    TestEqual(TEXT("Malformed evolution response is an error"), MalformedEvolutionError.Error, FString(TEXT("invalid_response")));

    return true;
}

#endif
