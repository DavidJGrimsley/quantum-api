#include "QuantumApiAsyncActions.h"

#include "QuantumApiClient.h"
#include "QuantumApiSettings.h"

UQuantumApiHealthAsyncAction* UQuantumApiHealthAsyncAction::HealthCheck(
    UObject* WorldContextObject,
    FQuantumApiRequestOptions Options
)
{
    UQuantumApiHealthAsyncAction* Action = NewObject<UQuantumApiHealthAsyncAction>();
    Action->RequestOptions = MoveTemp(Options);
    Action->RegisterWithGameInstance(WorldContextObject);
    return Action;
}

void UQuantumApiHealthAsyncAction::Activate()
{
    Client = MakeShared<FQuantumApiClient>(GetDefault<UQuantumApiSettings>());
    TWeakObjectPtr<UQuantumApiHealthAsyncAction> WeakThis(this);

    Client->HealthCheck(
        RequestOptions,
        FQuantumApiHealthDelegate::CreateLambda(
            [WeakThis](const FQuantumApiHealthResponse& Response)
            {
                if (!WeakThis.IsValid())
                {
                    return;
                }

                WeakThis->OnSuccess.Broadcast(Response);
                WeakThis->SetReadyToDestroy();
            }
        ),
        FQuantumApiErrorDelegate::CreateLambda(
            [WeakThis](const FQuantumApiError& Error)
            {
                if (!WeakThis.IsValid())
                {
                    return;
                }

                WeakThis->OnError.Broadcast(Error);
                WeakThis->SetReadyToDestroy();
            }
        )
    );
}

UQuantumApiRunGateAsyncAction* UQuantumApiRunGateAsyncAction::RunGate(
    UObject* WorldContextObject,
    FQuantumApiRunGateRequest Request,
    FQuantumApiRequestOptions Options
)
{
    UQuantumApiRunGateAsyncAction* Action = NewObject<UQuantumApiRunGateAsyncAction>();
    Action->GateRequest = MoveTemp(Request);
    Action->RequestOptions = MoveTemp(Options);
    Action->RegisterWithGameInstance(WorldContextObject);
    return Action;
}

void UQuantumApiRunGateAsyncAction::Activate()
{
    Client = MakeShared<FQuantumApiClient>(GetDefault<UQuantumApiSettings>());
    TWeakObjectPtr<UQuantumApiRunGateAsyncAction> WeakThis(this);

    Client->RunGate(
        GateRequest,
        RequestOptions,
        FQuantumApiRunGateDelegate::CreateLambda(
            [WeakThis](const FQuantumApiRunGateResponse& Response)
            {
                if (!WeakThis.IsValid())
                {
                    return;
                }

                WeakThis->OnSuccess.Broadcast(Response);
                WeakThis->SetReadyToDestroy();
            }
        ),
        FQuantumApiErrorDelegate::CreateLambda(
            [WeakThis](const FQuantumApiError& Error)
            {
                if (!WeakThis.IsValid())
                {
                    return;
                }

                WeakThis->OnError.Broadcast(Error);
                WeakThis->SetReadyToDestroy();
            }
        )
    );
}

UQuantumApiTransformTextAsyncAction* UQuantumApiTransformTextAsyncAction::TransformText(
    UObject* WorldContextObject,
    FQuantumApiTextTransformRequest Request,
    FQuantumApiRequestOptions Options
)
{
    UQuantumApiTransformTextAsyncAction* Action = NewObject<UQuantumApiTransformTextAsyncAction>();
    Action->TextRequest = MoveTemp(Request);
    Action->RequestOptions = MoveTemp(Options);
    Action->RegisterWithGameInstance(WorldContextObject);
    return Action;
}

void UQuantumApiTransformTextAsyncAction::Activate()
{
    Client = MakeShared<FQuantumApiClient>(GetDefault<UQuantumApiSettings>());
    TWeakObjectPtr<UQuantumApiTransformTextAsyncAction> WeakThis(this);

    Client->TransformText(
        TextRequest,
        RequestOptions,
        FQuantumApiTextTransformDelegate::CreateLambda(
            [WeakThis](const FQuantumApiTextTransformResponse& Response)
            {
                if (!WeakThis.IsValid())
                {
                    return;
                }

                WeakThis->OnSuccess.Broadcast(Response);
                WeakThis->SetReadyToDestroy();
            }
        ),
        FQuantumApiErrorDelegate::CreateLambda(
            [WeakThis](const FQuantumApiError& Error)
            {
                if (!WeakThis.IsValid())
                {
                    return;
                }

                WeakThis->OnError.Broadcast(Error);
                WeakThis->SetReadyToDestroy();
            }
        )
    );
}
