#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "QuantumApiTypes.h"
#include "QuantumApiSettings.generated.h"

UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "Quantum API"))
class QUANTUMAPI_API UQuantumApiSettings : public UDeveloperSettings
{
    GENERATED_BODY()

public:
    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API")
    FString BaseUrl = TEXT("http://127.0.0.1:8000/v1");

    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API")
    EQuantumApiAuthMode AuthMode = EQuantumApiAuthMode::BackendProxy;

    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API")
    FString ApiKey;

    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API")
    FString BearerToken;

    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API", meta = (ClampMin = "1.0"))
    float RequestTimeoutSeconds = 10.0f;

    UFUNCTION(BlueprintPure, Category = "Quantum API")
    FString GetNormalizedBaseUrl() const;
};
