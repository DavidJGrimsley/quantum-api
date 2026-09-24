// Copyright (c) 2026 David J. Grimsley. All rights reserved.
#include "QuantumApiDemoGameMode.h"

#include "Engine/World.h"
#include "QuantumApiDemoActor.h"

AQuantumApiDemoGameMode::AQuantumApiDemoGameMode()
{
    DemoActorClass = AQuantumApiDemoActor::StaticClass();
}

void AQuantumApiDemoGameMode::BeginPlay()
{
    Super::BeginPlay();
    if (DemoActorClass)
    {
        GetWorld()->SpawnActor<AQuantumApiDemoActor>(DemoActorClass, FVector::ZeroVector, FRotator::ZeroRotator);
    }
}
