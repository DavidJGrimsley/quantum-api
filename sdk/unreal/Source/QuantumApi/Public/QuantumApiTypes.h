#pragma once

#include "CoreMinimal.h"
#include "QuantumApiTypes.generated.h"

UENUM(BlueprintType)
enum class EQuantumApiAuthMode : uint8
{
    BackendProxy UMETA(DisplayName = "Backend Proxy"),
    DirectApiKey UMETA(DisplayName = "Direct API Key")
};

USTRUCT(BlueprintType)
struct FQuantumApiRequestOptions
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API")
    FString OverrideApiKey;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API")
    FString OverrideBearerToken;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API")
    TMap<FString, FString> ExtraHeaders;
};

USTRUCT(BlueprintType)
struct FQuantumApiError
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    int32 StatusCode = 0;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    FString Error;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    FString Message;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    FString RequestId;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    TMap<FString, FString> Headers;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    FString RawBody;
};

USTRUCT(BlueprintType)
struct FQuantumApiHealthResponse
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    FString Status;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    FString Service;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    FString Version;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    bool bQiskitAvailable = false;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    FString RuntimeMode;
};

USTRUCT(BlueprintType)
struct FQuantumApiRunGateRequest
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API")
    FString GateType = TEXT("bit_flip");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API")
    bool bSendRotationAngle = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API")
    double RotationAngleRad = 0.0;
};

USTRUCT(BlueprintType)
struct FQuantumApiRunGateResponse
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    FString GateType;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    int32 Measurement = 0;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    double SuperpositionStrength = 0.0;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    bool bSuccess = false;
};

USTRUCT(BlueprintType)
struct FQuantumApiTextTransformRequest
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API")
    FString Text;
};

USTRUCT(BlueprintType)
struct FQuantumApiTextTransformResponse
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    FString Original;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    FString Transformed;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    double CoveragePercent = 0.0;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    int32 QuantumWords = 0;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    int32 TotalWords = 0;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    TMap<FString, int32> CategoryCounts;
};
