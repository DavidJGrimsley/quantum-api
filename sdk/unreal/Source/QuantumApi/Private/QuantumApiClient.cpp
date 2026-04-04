#include "QuantumApiClient.h"

#include "Dom/JsonObject.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "JsonObjectConverter.h"
#include "QuantumApiSettings.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

namespace
{
FString SerializeJsonObject(const TSharedRef<FJsonObject>& JsonObject)
{
    FString Body;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Body);
    FJsonSerializer::Serialize(JsonObject, Writer);
    return Body;
}
}

FQuantumApiClient::FQuantumApiClient(const UQuantumApiSettings* InSettings)
    : BaseUrl(InSettings ? InSettings->GetNormalizedBaseUrl() : TEXT(""))
    , DefaultApiKey(InSettings ? InSettings->ApiKey : TEXT(""))
    , DefaultBearerToken(InSettings ? InSettings->BearerToken : TEXT(""))
    , AuthMode(InSettings ? InSettings->AuthMode : EQuantumApiAuthMode::BackendProxy)
    , RequestTimeoutSeconds(InSettings ? InSettings->RequestTimeoutSeconds : 10.0f)
{
}

void FQuantumApiClient::HealthCheck(
    const FQuantumApiRequestOptions& Options,
    FQuantumApiHealthDelegate OnSuccess,
    FQuantumApiErrorDelegate OnError
) const
{
    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest = BuildRequest(TEXT("/health"), TEXT("GET"), TEXT(""), Options);
    HttpRequest->OnProcessRequestComplete().BindLambda(
        [OnSuccess, OnError](FHttpRequestPtr, FHttpResponsePtr Response, bool bConnectedSuccessfully)
        {
            if (!bConnectedSuccessfully || !Response.IsValid())
            {
                OnError.ExecuteIfBound(BuildTransportError(TEXT("Network request failed.")));
                return;
            }

            if (!EHttpResponseCodes::IsOk(Response->GetResponseCode()))
            {
                OnError.ExecuteIfBound(BuildResponseError(Response));
                return;
            }

            FQuantumApiHealthResponse Payload;
            if (!FJsonObjectConverter::JsonObjectStringToUStruct(Response->GetContentAsString(), &Payload, 0, 0))
            {
                OnError.ExecuteIfBound(BuildTransportError(TEXT("Failed to parse health response JSON.")));
                return;
            }

            OnSuccess.ExecuteIfBound(Payload);
        }
    );
    HttpRequest->ProcessRequest();
}

void FQuantumApiClient::RunGate(
    const FQuantumApiRunGateRequest& Request,
    const FQuantumApiRequestOptions& Options,
    FQuantumApiRunGateDelegate OnSuccess,
    FQuantumApiErrorDelegate OnError
) const
{
    TSharedRef<FJsonObject> JsonObject = MakeShared<FJsonObject>();
    JsonObject->SetStringField(TEXT("gate_type"), Request.GateType);
    if (Request.bSendRotationAngle)
    {
        JsonObject->SetNumberField(TEXT("rotation_angle_rad"), Request.RotationAngleRad);
    }

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest = BuildRequest(
        TEXT("/gates/run"),
        TEXT("POST"),
        SerializeJsonObject(JsonObject),
        Options
    );
    HttpRequest->OnProcessRequestComplete().BindLambda(
        [OnSuccess, OnError](FHttpRequestPtr, FHttpResponsePtr Response, bool bConnectedSuccessfully)
        {
            if (!bConnectedSuccessfully || !Response.IsValid())
            {
                OnError.ExecuteIfBound(BuildTransportError(TEXT("Network request failed.")));
                return;
            }

            if (!EHttpResponseCodes::IsOk(Response->GetResponseCode()))
            {
                OnError.ExecuteIfBound(BuildResponseError(Response));
                return;
            }

            FQuantumApiRunGateResponse Payload;
            if (!FJsonObjectConverter::JsonObjectStringToUStruct(Response->GetContentAsString(), &Payload, 0, 0))
            {
                OnError.ExecuteIfBound(BuildTransportError(TEXT("Failed to parse gate response JSON.")));
                return;
            }

            OnSuccess.ExecuteIfBound(Payload);
        }
    );
    HttpRequest->ProcessRequest();
}

void FQuantumApiClient::TransformText(
    const FQuantumApiTextTransformRequest& Request,
    const FQuantumApiRequestOptions& Options,
    FQuantumApiTextTransformDelegate OnSuccess,
    FQuantumApiErrorDelegate OnError
) const
{
    TSharedRef<FJsonObject> JsonObject = MakeShared<FJsonObject>();
    JsonObject->SetStringField(TEXT("text"), Request.Text);

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest = BuildRequest(
        TEXT("/text/transform"),
        TEXT("POST"),
        SerializeJsonObject(JsonObject),
        Options
    );
    HttpRequest->OnProcessRequestComplete().BindLambda(
        [OnSuccess, OnError](FHttpRequestPtr, FHttpResponsePtr Response, bool bConnectedSuccessfully)
        {
            if (!bConnectedSuccessfully || !Response.IsValid())
            {
                OnError.ExecuteIfBound(BuildTransportError(TEXT("Network request failed.")));
                return;
            }

            if (!EHttpResponseCodes::IsOk(Response->GetResponseCode()))
            {
                OnError.ExecuteIfBound(BuildResponseError(Response));
                return;
            }

            FQuantumApiTextTransformResponse Payload;
            if (!FJsonObjectConverter::JsonObjectStringToUStruct(Response->GetContentAsString(), &Payload, 0, 0))
            {
                OnError.ExecuteIfBound(BuildTransportError(TEXT("Failed to parse text transform response JSON.")));
                return;
            }

            OnSuccess.ExecuteIfBound(Payload);
        }
    );
    HttpRequest->ProcessRequest();
}

TSharedRef<IHttpRequest, ESPMode::ThreadSafe> FQuantumApiClient::BuildRequest(
    const FString& Path,
    const FString& Verb,
    const FString& Body,
    const FQuantumApiRequestOptions& Options
) const
{
    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest = FHttpModule::Get().CreateRequest();
    HttpRequest->SetURL(BaseUrl + Path);
    HttpRequest->SetVerb(Verb);
    HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    HttpRequest->SetTimeout(RequestTimeoutSeconds);

    const FString ApiKey = !Options.OverrideApiKey.IsEmpty() ? Options.OverrideApiKey : DefaultApiKey;
    const FString BearerToken = !Options.OverrideBearerToken.IsEmpty() ? Options.OverrideBearerToken : DefaultBearerToken;

    if (!ApiKey.IsEmpty() && AuthMode == EQuantumApiAuthMode::DirectApiKey)
    {
        HttpRequest->SetHeader(TEXT("X-API-Key"), ApiKey);
    }

    if (!BearerToken.IsEmpty())
    {
        HttpRequest->SetHeader(TEXT("Authorization"), FString::Printf(TEXT("Bearer %s"), *BearerToken));
    }

    for (const TPair<FString, FString>& Header : Options.ExtraHeaders)
    {
        HttpRequest->SetHeader(Header.Key, Header.Value);
    }

    if (!Body.IsEmpty())
    {
        HttpRequest->SetContentAsString(Body);
    }

    return HttpRequest;
}

FQuantumApiError FQuantumApiClient::BuildTransportError(const FString& Message)
{
    FQuantumApiError Error;
    Error.StatusCode = 0;
    Error.Error = TEXT("transport_error");
    Error.Message = Message;
    return Error;
}

FQuantumApiError FQuantumApiClient::BuildResponseError(const FHttpResponsePtr& Response)
{
    FQuantumApiError Error;
    Error.StatusCode = Response.IsValid() ? Response->GetResponseCode() : 0;
    Error.Headers = ExtractHeaders(Response);
    Error.RawBody = Response.IsValid() ? Response->GetContentAsString() : TEXT("");

    TSharedPtr<FJsonObject> JsonObject;
    if (Response.IsValid())
    {
        const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Response->GetContentAsString());
        if (FJsonSerializer::Deserialize(Reader, JsonObject) && JsonObject.IsValid())
        {
            JsonObject->TryGetStringField(TEXT("error"), Error.Error);
            JsonObject->TryGetStringField(TEXT("message"), Error.Message);
            JsonObject->TryGetStringField(TEXT("request_id"), Error.RequestId);
        }
    }

    if (Error.Error.IsEmpty())
    {
        Error.Error = TEXT("http_error");
    }

    if (Error.Message.IsEmpty())
    {
        Error.Message = TEXT("Quantum API request failed.");
    }

    return Error;
}

TMap<FString, FString> FQuantumApiClient::ExtractHeaders(const FHttpResponsePtr& Response)
{
    TMap<FString, FString> Headers;
    if (!Response.IsValid())
    {
        return Headers;
    }

    for (const FString& HeaderLine : Response->GetAllHeaders())
    {
        FString Key;
        FString Value;
        if (HeaderLine.Split(TEXT(":"), &Key, &Value))
        {
            Headers.Add(Key.TrimStartAndEnd(), Value.TrimStartAndEnd());
        }
    }
    return Headers;
}
