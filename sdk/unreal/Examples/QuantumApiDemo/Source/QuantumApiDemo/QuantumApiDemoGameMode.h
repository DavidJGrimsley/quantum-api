// Copyright (c) 2026 David J. Grimsley. All rights reserved.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "QuantumApiDemoGameMode.generated.h"

class AQuantumApiDemoActor;

UCLASS()
class QUANTUMAPIDEMO_API AQuantumApiDemoGameMode : public AGameModeBase
{
    GENERATED_BODY()

public:
    AQuantumApiDemoGameMode();

    /** Override this with a Blueprint child to customize the visible demo flow. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Quantum API Demo")
    TSubclassOf<AQuantumApiDemoActor> DemoActorClass;

protected:
    virtual void BeginPlay() override;
};
