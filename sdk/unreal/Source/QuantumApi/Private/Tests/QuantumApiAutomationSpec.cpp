#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "QuantumApiClient.h"
#include "QuantumApiSettings.h"

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
    Settings->BaseUrl = TEXT("https://example.test/v1");
    Settings->AuthMode = AuthMode;
    Settings->ApiKey = TEXT("unit-test-key");
    Settings->bUseEnvironmentApiKey = false;
    Settings->DefaultIbmProfile = TEXT("IBM Open");
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
    UQuantumApiSettings* UrlSettings = NewObject<UQuantumApiSettings>();
    UrlSettings->BaseUrl = TEXT("https://example.test/v1/");
    TestEqual(TEXT("Base URL preserves HTTPS scheme and removes one trailing slash"), UrlSettings->GetNormalizedBaseUrl(), FString(TEXT("https://example.test/v1")));

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
    TestEqual(TEXT("Gate URL"), Mock->Requests[0].Url, FString(TEXT("https://example.test/v1/gates/run")));
    TestEqual(TEXT("Gate verb"), Mock->Requests[0].Verb, FString(TEXT("POST")));
    TestEqual(TEXT("Direct API key header"), Mock->Requests[0].Headers.FindRef(TEXT("X-API-Key")), FString(TEXT("unit-test-key")));
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
    HardwareRequest.BackendName = TEXT("ibm_kingston");
    HardwareClient.SubmitRandomJob(HardwareRequest, FQuantumApiRequestOptions(), FQuantumApiJsonDelegate(), FQuantumApiErrorDelegate());
    TestTrue(TEXT("IBM random job uses configured profile fallback"), HardwareMock->Requests[0].Body.Contains(TEXT("\"ibm_profile\":\"IBM Open\"")));

    return true;
}

#endif
