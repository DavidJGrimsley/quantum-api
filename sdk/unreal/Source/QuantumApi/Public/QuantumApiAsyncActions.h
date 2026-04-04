#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintAsyncActionBase.h"
#include "QuantumApiTypes.h"
#include "QuantumApiAsyncActions.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FQuantumApiHealthSuccessSignature, FQuantumApiHealthResponse, Response);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FQuantumApiRunGateSuccessSignature, FQuantumApiRunGateResponse, Response);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FQuantumApiTextTransformSuccessSignature, FQuantumApiTextTransformResponse, Response);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FQuantumApiFailureSignature, FQuantumApiError, Error);

UCLASS()
class QUANTUMAPI_API UQuantumApiHealthAsyncAction : public UBlueprintAsyncActionBase
{
    GENERATED_BODY()

public:
    UPROPERTY(BlueprintAssignable)
    FQuantumApiHealthSuccessSignature OnSuccess;

    UPROPERTY(BlueprintAssignable)
    FQuantumApiFailureSignature OnError;

    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"))
    static UQuantumApiHealthAsyncAction* HealthCheck(UObject* WorldContextObject, FQuantumApiRequestOptions Options);

    virtual void Activate() override;

private:
    FQuantumApiRequestOptions RequestOptions;
    TSharedPtr<class FQuantumApiClient> Client;
};

UCLASS()
class QUANTUMAPI_API UQuantumApiRunGateAsyncAction : public UBlueprintAsyncActionBase
{
    GENERATED_BODY()

public:
    UPROPERTY(BlueprintAssignable)
    FQuantumApiRunGateSuccessSignature OnSuccess;

    UPROPERTY(BlueprintAssignable)
    FQuantumApiFailureSignature OnError;

    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"))
    static UQuantumApiRunGateAsyncAction* RunGate(
        UObject* WorldContextObject,
        FQuantumApiRunGateRequest Request,
        FQuantumApiRequestOptions Options
    );

    virtual void Activate() override;

private:
    FQuantumApiRunGateRequest GateRequest;
    FQuantumApiRequestOptions RequestOptions;
    TSharedPtr<class FQuantumApiClient> Client;
};

UCLASS()
class QUANTUMAPI_API UQuantumApiTransformTextAsyncAction : public UBlueprintAsyncActionBase
{
    GENERATED_BODY()

public:
    UPROPERTY(BlueprintAssignable)
    FQuantumApiTextTransformSuccessSignature OnSuccess;

    UPROPERTY(BlueprintAssignable)
    FQuantumApiFailureSignature OnError;

    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"))
    static UQuantumApiTransformTextAsyncAction* TransformText(
        UObject* WorldContextObject,
        FQuantumApiTextTransformRequest Request,
        FQuantumApiRequestOptions Options
    );

    virtual void Activate() override;

private:
    FQuantumApiTextTransformRequest TextRequest;
    FQuantumApiRequestOptions RequestOptions;
    TSharedPtr<class FQuantumApiClient> Client;
};
