#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "QuantumApiTypes.h"
#include "QuantumApiDemoActor.generated.h"

UCLASS(Blueprintable)
class QUANTUMAPIDEMO_API AQuantumApiDemoActor : public AActor
{
    GENERATED_BODY()

public:
    AQuantumApiDemoActor();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API Demo")
    bool bRunDemoOnBeginPlay = true;

    /** The same callable sequence can be authored in a Blueprint subclass. */
    UFUNCTION(BlueprintCallable, Category = "Quantum API Demo")
    void RunQuickstart();

protected:
    virtual void BeginPlay() override;

private:
    UFUNCTION()
    void HandleHealth(FQuantumApiHealthResponse Response);
    UFUNCTION()
    void HandleGate(FQuantumApiRunGateResponse Response);
    UFUNCTION()
    void HandleRandom(FQuantumApiRandomIntResponse Response);
    UFUNCTION()
    void HandleError(FQuantumApiError Error);
    void ShowMessage(const FString& Message, const FColor& Color) const;

    UPROPERTY(Transient)
    TObjectPtr<UObject> ActiveAction;
};
