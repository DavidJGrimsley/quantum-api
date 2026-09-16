#include "QuantumApiDemoActor.h"

#include "Engine/Engine.h"
#include "QuantumApiAsyncActions.h"

AQuantumApiDemoActor::AQuantumApiDemoActor()
{
    PrimaryActorTick.bCanEverTick = false;
}

void AQuantumApiDemoActor::BeginPlay()
{
    Super::BeginPlay();
    if (bRunDemoOnBeginPlay) RunQuickstart();
}

void AQuantumApiDemoActor::RunQuickstart()
{
    const FQuantumApiRequestOptions Options;
    UQuantumApiHealthAsyncAction* Action = UQuantumApiHealthAsyncAction::HealthCheck(this, Options);
    ActiveAction = Action;
    Action->OnSuccess.AddDynamic(this, &AQuantumApiDemoActor::HandleHealth);
    Action->OnError.AddDynamic(this, &AQuantumApiDemoActor::HandleError);
    Action->Activate();
    ShowMessage(TEXT("Quantum API: checking service health..."), FColor::Cyan);
}

void AQuantumApiDemoActor::HandleHealth(FQuantumApiHealthResponse Response)
{
    ShowMessage(FString::Printf(TEXT("Health OK: %s (%s)"), *Response.Service, *Response.RuntimeMode), FColor::Green);
    FQuantumApiRunGateRequest Request;
    Request.GateType = TEXT("rotation");
    Request.bSendRotationAngle = true;
    Request.RotationAngleRad = PI / 2.0;
    const FQuantumApiRequestOptions Options;
    UQuantumApiRunGateAsyncAction* Action = UQuantumApiRunGateAsyncAction::RunGate(this, Request, Options);
    ActiveAction = Action;
    Action->OnSuccess.AddDynamic(this, &AQuantumApiDemoActor::HandleGate);
    Action->OnError.AddDynamic(this, &AQuantumApiDemoActor::HandleError);
    Action->Activate();
}

void AQuantumApiDemoActor::HandleGate(FQuantumApiRunGateResponse Response)
{
    ShowMessage(FString::Printf(TEXT("RY(pi/2): measurement %d"), Response.Measurement), FColor::Green);
    const FQuantumApiRandomIntRequest Request;
    const FQuantumApiRequestOptions Options;
    UQuantumApiRandomIntAsyncAction* Action = UQuantumApiRandomIntAsyncAction::GenerateRandomInt(this, Request, Options);
    ActiveAction = Action;
    Action->OnSuccess.AddDynamic(this, &AQuantumApiDemoActor::HandleRandom);
    Action->OnError.AddDynamic(this, &AQuantumApiDemoActor::HandleError);
    Action->Activate();
}

void AQuantumApiDemoActor::HandleRandom(FQuantumApiRandomIntResponse Response)
{
    ShowMessage(FString::Printf(TEXT("QRNG %d (%s)"), Response.Value, *Response.Source), FColor::Green);
}

void AQuantumApiDemoActor::HandleError(FQuantumApiError Error)
{
    ShowMessage(FString::Printf(TEXT("Quantum API error %d: %s"), Error.StatusCode, *Error.Message), FColor::Red);
}

void AQuantumApiDemoActor::ShowMessage(const FString& Message, const FColor& Color) const
{
    UE_LOG(LogTemp, Display, TEXT("%s"), *Message);
    if (GEngine) GEngine->AddOnScreenDebugMessage(-1, 8.0f, Color, Message);
}
