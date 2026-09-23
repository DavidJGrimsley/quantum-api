// Copyright (c) 2026 David J. Grimsley. All rights reserved.
#include "QuantumApiAsyncActions.h"

#include "QuantumApiClient.h"
#include "QuantumApiSettings.h"

namespace
{
template <typename TAction>
TAction* RegisterAction(UObject* WorldContextObject)
{
    TAction* Action = NewObject<TAction>();
    Action->RegisterWithGameInstance(WorldContextObject);
    return Action;
}
}

UQuantumApiHealthAsyncAction* UQuantumApiHealthAsyncAction::HealthCheck(UObject* WorldContextObject, FQuantumApiRequestOptions Options)
{
    UQuantumApiHealthAsyncAction* Action = RegisterAction<UQuantumApiHealthAsyncAction>(WorldContextObject);
    Action->RequestOptions = MoveTemp(Options);
    return Action;
}

void UQuantumApiHealthAsyncAction::Activate()
{
    Client = MakeShared<FQuantumApiClient>(GetDefault<UQuantumApiSettings>());
    const TWeakObjectPtr<UQuantumApiHealthAsyncAction> WeakThis(this);
    Client->HealthCheck(RequestOptions,
        FQuantumApiHealthDelegate::CreateLambda([WeakThis](const FQuantumApiHealthResponse& Response)
        {
            if (!WeakThis.IsValid()) return;
            WeakThis->OnSuccess.Broadcast(Response);
            WeakThis->SetReadyToDestroy();
        }),
        FQuantumApiErrorDelegate::CreateLambda([WeakThis](const FQuantumApiError& Error)
        {
            if (!WeakThis.IsValid()) return;
            WeakThis->OnError.Broadcast(Error);
            WeakThis->SetReadyToDestroy();
        }));
}

UQuantumApiRunGateAsyncAction* UQuantumApiRunGateAsyncAction::RunGate(UObject* WorldContextObject, FQuantumApiRunGateRequest Request, FQuantumApiRequestOptions Options)
{
    UQuantumApiRunGateAsyncAction* Action = RegisterAction<UQuantumApiRunGateAsyncAction>(WorldContextObject);
    Action->GateRequest = MoveTemp(Request);
    Action->RequestOptions = MoveTemp(Options);
    return Action;
}

void UQuantumApiRunGateAsyncAction::Activate()
{
    Client = MakeShared<FQuantumApiClient>(GetDefault<UQuantumApiSettings>());
    const TWeakObjectPtr<UQuantumApiRunGateAsyncAction> WeakThis(this);
    Client->RunGate(GateRequest, RequestOptions,
        FQuantumApiRunGateDelegate::CreateLambda([WeakThis](const FQuantumApiRunGateResponse& Response)
        {
            if (!WeakThis.IsValid()) return;
            WeakThis->OnSuccess.Broadcast(Response);
            WeakThis->SetReadyToDestroy();
        }),
        FQuantumApiErrorDelegate::CreateLambda([WeakThis](const FQuantumApiError& Error)
        {
            if (!WeakThis.IsValid()) return;
            WeakThis->OnError.Broadcast(Error);
            WeakThis->SetReadyToDestroy();
        }));
}

UQuantumApiTransformTextAsyncAction* UQuantumApiTransformTextAsyncAction::TransformText(UObject* WorldContextObject, FQuantumApiTextTransformRequest Request, FQuantumApiRequestOptions Options)
{
    UQuantumApiTransformTextAsyncAction* Action = RegisterAction<UQuantumApiTransformTextAsyncAction>(WorldContextObject);
    Action->TextRequest = MoveTemp(Request);
    Action->RequestOptions = MoveTemp(Options);
    return Action;
}

void UQuantumApiTransformTextAsyncAction::Activate()
{
    Client = MakeShared<FQuantumApiClient>(GetDefault<UQuantumApiSettings>());
    const TWeakObjectPtr<UQuantumApiTransformTextAsyncAction> WeakThis(this);
    Client->TransformText(TextRequest, RequestOptions,
        FQuantumApiTextTransformDelegate::CreateLambda([WeakThis](const FQuantumApiTextTransformResponse& Response)
        {
            if (!WeakThis.IsValid()) return;
            WeakThis->OnSuccess.Broadcast(Response);
            WeakThis->SetReadyToDestroy();
        }),
        FQuantumApiErrorDelegate::CreateLambda([WeakThis](const FQuantumApiError& Error)
        {
            if (!WeakThis.IsValid()) return;
            WeakThis->OnError.Broadcast(Error);
            WeakThis->SetReadyToDestroy();
        }));
}

UQuantumApiRandomIntAsyncAction* UQuantumApiRandomIntAsyncAction::GenerateRandomInt(UObject* WorldContextObject, FQuantumApiRandomIntRequest Request, FQuantumApiRequestOptions Options)
{
    UQuantumApiRandomIntAsyncAction* Action = RegisterAction<UQuantumApiRandomIntAsyncAction>(WorldContextObject);
    Action->RandomRequest = MoveTemp(Request);
    Action->RequestOptions = MoveTemp(Options);
    return Action;
}

void UQuantumApiRandomIntAsyncAction::Activate()
{
    Client = MakeShared<FQuantumApiClient>(GetDefault<UQuantumApiSettings>());
    const TWeakObjectPtr<UQuantumApiRandomIntAsyncAction> WeakThis(this);
    Client->GenerateRandomInt(RandomRequest, RequestOptions,
        FQuantumApiRandomIntDelegate::CreateLambda([WeakThis](const FQuantumApiRandomIntResponse& Response)
        {
            if (!WeakThis.IsValid()) return;
            WeakThis->OnSuccess.Broadcast(Response);
            WeakThis->SetReadyToDestroy();
        }),
        FQuantumApiErrorDelegate::CreateLambda([WeakThis](const FQuantumApiError& Error)
        {
            if (!WeakThis.IsValid()) return;
            WeakThis->OnError.Broadcast(Error);
            WeakThis->SetReadyToDestroy();
        }));
}

UQuantumApiJsonAsyncAction* UQuantumApiJsonAsyncAction::Create(UObject* WorldContextObject, EActionKind Kind, FQuantumApiRequestOptions Options)
{
    UQuantumApiJsonAsyncAction* Action = RegisterAction<UQuantumApiJsonAsyncAction>(WorldContextObject);
    Action->ActionKind = Kind;
    Action->RequestOptions = MoveTemp(Options);
    return Action;
}

UQuantumApiJsonAsyncAction* UQuantumApiJsonAsyncAction::GetEchoTypes(UObject* WorldContextObject, FQuantumApiRequestOptions Options)
{
    return Create(WorldContextObject, EActionKind::EchoTypes, MoveTemp(Options));
}

UQuantumApiJsonAsyncAction* UQuantumApiJsonAsyncAction::RunCircuit(UObject* WorldContextObject, FQuantumApiCircuitRunRequest Request, FQuantumApiRequestOptions Options)
{
    UQuantumApiJsonAsyncAction* Action = Create(WorldContextObject, EActionKind::Circuit, MoveTemp(Options));
    Action->CircuitRequest = MoveTemp(Request);
    return Action;
}

UQuantumApiJsonAsyncAction* UQuantumApiJsonAsyncAction::ListBackends(UObject* WorldContextObject, FQuantumApiBackendListRequest Request, FQuantumApiRequestOptions Options)
{
    UQuantumApiJsonAsyncAction* Action = Create(WorldContextObject, EActionKind::Backends, MoveTemp(Options));
    Action->BackendRequest = MoveTemp(Request);
    return Action;
}

UQuantumApiJsonAsyncAction* UQuantumApiJsonAsyncAction::Transpile(UObject* WorldContextObject, FQuantumApiTranspileRequest Request, FQuantumApiRequestOptions Options)
{
    UQuantumApiJsonAsyncAction* Action = Create(WorldContextObject, EActionKind::Transpile, MoveTemp(Options));
    Action->TranspileRequest = MoveTemp(Request);
    return Action;
}

UQuantumApiJsonAsyncAction* UQuantumApiJsonAsyncAction::ImportQasm(UObject* WorldContextObject, FQuantumApiQasmRequest Request, FQuantumApiRequestOptions Options)
{
    UQuantumApiJsonAsyncAction* Action = Create(WorldContextObject, EActionKind::ImportQasm, MoveTemp(Options));
    Action->QasmRequest = MoveTemp(Request);
    return Action;
}

UQuantumApiJsonAsyncAction* UQuantumApiJsonAsyncAction::ExportQasm(UObject* WorldContextObject, FQuantumApiCircuitDefinition Circuit, FString QasmVersion, FQuantumApiRequestOptions Options)
{
    UQuantumApiJsonAsyncAction* Action = Create(WorldContextObject, EActionKind::ExportQasm, MoveTemp(Options));
    Action->ExportCircuit = MoveTemp(Circuit);
    Action->ExportQasmVersion = MoveTemp(QasmVersion);
    return Action;
}

UQuantumApiJsonAsyncAction* UQuantumApiJsonAsyncAction::RunQasm(UObject* WorldContextObject, FQuantumApiQasmRunRequest Request, FQuantumApiRequestOptions Options)
{
    UQuantumApiJsonAsyncAction* Action = Create(WorldContextObject, EActionKind::RunQasm, MoveTemp(Options));
    Action->QasmRunRequest = MoveTemp(Request);
    return Action;
}

UQuantumApiJsonAsyncAction* UQuantumApiJsonAsyncAction::SubmitCircuitJob(UObject* WorldContextObject, FQuantumApiCircuitJobRequest Request, FQuantumApiRequestOptions Options)
{
    UQuantumApiJsonAsyncAction* Action = Create(WorldContextObject, EActionKind::CircuitJob, MoveTemp(Options));
    Action->CircuitJobRequest = MoveTemp(Request);
    return Action;
}

UQuantumApiJsonAsyncAction* UQuantumApiJsonAsyncAction::SubmitQasmJob(UObject* WorldContextObject, FQuantumApiQasmJobRequest Request, FQuantumApiRequestOptions Options)
{
    UQuantumApiJsonAsyncAction* Action = Create(WorldContextObject, EActionKind::QasmJob, MoveTemp(Options));
    Action->QasmJobRequest = MoveTemp(Request);
    return Action;
}

UQuantumApiJsonAsyncAction* UQuantumApiJsonAsyncAction::SubmitRandomJob(UObject* WorldContextObject, FQuantumApiRandomJobRequest Request, FQuantumApiRequestOptions Options)
{
    UQuantumApiJsonAsyncAction* Action = Create(WorldContextObject, EActionKind::RandomJob, MoveTemp(Options));
    Action->RandomJobRequest = MoveTemp(Request);
    return Action;
}

UQuantumApiJsonAsyncAction* UQuantumApiJsonAsyncAction::GetJobStatus(UObject* WorldContextObject, FString InJobId, FQuantumApiRequestOptions Options)
{
    UQuantumApiJsonAsyncAction* Action = Create(WorldContextObject, EActionKind::JobStatus, MoveTemp(Options));
    Action->JobId = MoveTemp(InJobId);
    return Action;
}

UQuantumApiJsonAsyncAction* UQuantumApiJsonAsyncAction::GetJobResult(UObject* WorldContextObject, FString InJobId, FQuantumApiRequestOptions Options)
{
    UQuantumApiJsonAsyncAction* Action = Create(WorldContextObject, EActionKind::JobResult, MoveTemp(Options));
    Action->JobId = MoveTemp(InJobId);
    return Action;
}

UQuantumApiJsonAsyncAction* UQuantumApiJsonAsyncAction::CancelJob(UObject* WorldContextObject, FString InJobId, FQuantumApiRequestOptions Options)
{
    UQuantumApiJsonAsyncAction* Action = Create(WorldContextObject, EActionKind::CancelJob, MoveTemp(Options));
    Action->JobId = MoveTemp(InJobId);
    return Action;
}

UQuantumApiJsonAsyncAction* UQuantumApiJsonAsyncAction::CallAdvancedJson(UObject* WorldContextObject, FQuantumApiAdvancedRequest Request, FQuantumApiRequestOptions Options)
{
    UQuantumApiJsonAsyncAction* Action = Create(WorldContextObject, EActionKind::Advanced, MoveTemp(Options));
    Action->AdvancedRequest = MoveTemp(Request);
    return Action;
}

void UQuantumApiJsonAsyncAction::Activate()
{
    Client = MakeShared<FQuantumApiClient>(GetDefault<UQuantumApiSettings>());
    const TWeakObjectPtr<UQuantumApiJsonAsyncAction> WeakThis(this);
    const FQuantumApiJsonDelegate Success = FQuantumApiJsonDelegate::CreateLambda([WeakThis](const FQuantumApiJsonResponse& Response)
    {
        if (!WeakThis.IsValid()) return;
        WeakThis->OnSuccess.Broadcast(Response);
        WeakThis->SetReadyToDestroy();
    });
    const FQuantumApiErrorDelegate Failure = FQuantumApiErrorDelegate::CreateLambda([WeakThis](const FQuantumApiError& Error)
    {
        if (!WeakThis.IsValid()) return;
        WeakThis->OnError.Broadcast(Error);
        WeakThis->SetReadyToDestroy();
    });

    switch (ActionKind)
    {
    case EActionKind::EchoTypes: Client->GetEchoTypes(RequestOptions, Success, Failure); break;
    case EActionKind::Circuit: Client->RunCircuit(CircuitRequest, RequestOptions, Success, Failure); break;
    case EActionKind::Backends: Client->ListBackends(BackendRequest, RequestOptions, Success, Failure); break;
    case EActionKind::Transpile: Client->Transpile(TranspileRequest, RequestOptions, Success, Failure); break;
    case EActionKind::ImportQasm: Client->ImportQasm(QasmRequest, RequestOptions, Success, Failure); break;
    case EActionKind::ExportQasm: Client->ExportQasm(ExportCircuit, ExportQasmVersion, RequestOptions, Success, Failure); break;
    case EActionKind::RunQasm: Client->RunQasm(QasmRunRequest, RequestOptions, Success, Failure); break;
    case EActionKind::CircuitJob: Client->SubmitCircuitJob(CircuitJobRequest, RequestOptions, Success, Failure); break;
    case EActionKind::QasmJob: Client->SubmitQasmJob(QasmJobRequest, RequestOptions, Success, Failure); break;
    case EActionKind::RandomJob: Client->SubmitRandomJob(RandomJobRequest, RequestOptions, Success, Failure); break;
    case EActionKind::JobStatus: Client->GetJobStatus(JobId, RequestOptions, Success, Failure); break;
    case EActionKind::JobResult: Client->GetJobResult(JobId, RequestOptions, Success, Failure); break;
    case EActionKind::CancelJob: Client->CancelJob(JobId, RequestOptions, Success, Failure); break;
    case EActionKind::Advanced: Client->CallAdvanced(AdvancedRequest, RequestOptions, Success, Failure); break;
    default: OnError.Broadcast(FQuantumApiError()); SetReadyToDestroy(); break;
    }
}
