// Copyright (c) 2026 David J. Grimsley. All rights reserved.
#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintAsyncActionBase.h"
#include "QuantumApiTypes.h"
#include "QuantumApiAsyncActions.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FQuantumApiHealthSuccessSignature, FQuantumApiHealthResponse, Response);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FQuantumApiRunGateSuccessSignature, FQuantumApiRunGateResponse, Response);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FQuantumApiTextTransformSuccessSignature, FQuantumApiTextTransformResponse, Response);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FQuantumApiRandomIntSuccessSignature, FQuantumApiRandomIntResponse, Response);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FQuantumApiJsonSuccessSignature, FQuantumApiJsonResponse, Response);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FQuantumApiFailureSignature, FQuantumApiError, Error);

UCLASS()
class QUANTUMAPI_API UQuantumApiHealthAsyncAction : public UBlueprintAsyncActionBase
{
    GENERATED_BODY()
public:
    UPROPERTY(BlueprintAssignable) FQuantumApiHealthSuccessSignature OnSuccess;
    UPROPERTY(BlueprintAssignable) FQuantumApiFailureSignature OnError;
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"), Category = "Quantum API")
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
    UPROPERTY(BlueprintAssignable) FQuantumApiRunGateSuccessSignature OnSuccess;
    UPROPERTY(BlueprintAssignable) FQuantumApiFailureSignature OnError;
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"), Category = "Quantum API")
    static UQuantumApiRunGateAsyncAction* RunGate(UObject* WorldContextObject, FQuantumApiRunGateRequest Request, FQuantumApiRequestOptions Options);
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
    UPROPERTY(BlueprintAssignable) FQuantumApiTextTransformSuccessSignature OnSuccess;
    UPROPERTY(BlueprintAssignable) FQuantumApiFailureSignature OnError;
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"), Category = "Quantum API")
    static UQuantumApiTransformTextAsyncAction* TransformText(UObject* WorldContextObject, FQuantumApiTextTransformRequest Request, FQuantumApiRequestOptions Options);
    virtual void Activate() override;
private:
    FQuantumApiTextTransformRequest TextRequest;
    FQuantumApiRequestOptions RequestOptions;
    TSharedPtr<class FQuantumApiClient> Client;
};

UCLASS()
class QUANTUMAPI_API UQuantumApiRandomIntAsyncAction : public UBlueprintAsyncActionBase
{
    GENERATED_BODY()
public:
    UPROPERTY(BlueprintAssignable) FQuantumApiRandomIntSuccessSignature OnSuccess;
    UPROPERTY(BlueprintAssignable) FQuantumApiFailureSignature OnError;
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"), Category = "Quantum API|QRNG")
    static UQuantumApiRandomIntAsyncAction* GenerateRandomInt(UObject* WorldContextObject, FQuantumApiRandomIntRequest Request, FQuantumApiRequestOptions Options);
    virtual void Activate() override;
private:
    FQuantumApiRandomIntRequest RandomRequest;
    FQuantumApiRequestOptions RequestOptions;
    TSharedPtr<class FQuantumApiClient> Client;
};

/**
 * Named Blueprint actions with typed request structs and raw JSON responses for complex contracts.
 * Use CallAdvancedJson for the 22 fixed rich-domain endpoints; it cannot call account/credential routes.
 */
UCLASS()
class QUANTUMAPI_API UQuantumApiJsonAsyncAction : public UBlueprintAsyncActionBase
{
    GENERATED_BODY()
public:
    UPROPERTY(BlueprintAssignable) FQuantumApiJsonSuccessSignature OnSuccess;
    UPROPERTY(BlueprintAssignable) FQuantumApiFailureSignature OnError;

    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"), Category = "Quantum API")
    static UQuantumApiJsonAsyncAction* GetEchoTypes(UObject* WorldContextObject, FQuantumApiRequestOptions Options);
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"), Category = "Quantum API|Circuits")
    static UQuantumApiJsonAsyncAction* RunCircuit(UObject* WorldContextObject, FQuantumApiCircuitRunRequest Request, FQuantumApiRequestOptions Options);
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"), Category = "Quantum API|Runtime")
    static UQuantumApiJsonAsyncAction* ListBackends(UObject* WorldContextObject, FQuantumApiBackendListRequest Request, FQuantumApiRequestOptions Options);
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"), Category = "Quantum API|Runtime")
    static UQuantumApiJsonAsyncAction* Transpile(UObject* WorldContextObject, FQuantumApiTranspileRequest Request, FQuantumApiRequestOptions Options);
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"), Category = "Quantum API|QASM")
    static UQuantumApiJsonAsyncAction* ImportQasm(UObject* WorldContextObject, FQuantumApiQasmRequest Request, FQuantumApiRequestOptions Options);
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"), Category = "Quantum API|QASM")
    static UQuantumApiJsonAsyncAction* ExportQasm(UObject* WorldContextObject, FQuantumApiCircuitDefinition Circuit, FString QasmVersion, FQuantumApiRequestOptions Options);
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"), Category = "Quantum API|QASM")
    static UQuantumApiJsonAsyncAction* RunQasm(UObject* WorldContextObject, FQuantumApiQasmRunRequest Request, FQuantumApiRequestOptions Options);
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"), Category = "Quantum API|Jobs")
    static UQuantumApiJsonAsyncAction* SubmitCircuitJob(UObject* WorldContextObject, FQuantumApiCircuitJobRequest Request, FQuantumApiRequestOptions Options);
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"), Category = "Quantum API|Jobs")
    static UQuantumApiJsonAsyncAction* SubmitQasmJob(UObject* WorldContextObject, FQuantumApiQasmJobRequest Request, FQuantumApiRequestOptions Options);
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"), Category = "Quantum API|QRNG")
    static UQuantumApiJsonAsyncAction* SubmitRandomJob(UObject* WorldContextObject, FQuantumApiRandomJobRequest Request, FQuantumApiRequestOptions Options);
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"), Category = "Quantum API|Jobs")
    static UQuantumApiJsonAsyncAction* GetJobStatus(UObject* WorldContextObject, FString JobId, FQuantumApiRequestOptions Options);
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"), Category = "Quantum API|Jobs")
    static UQuantumApiJsonAsyncAction* GetJobResult(UObject* WorldContextObject, FString JobId, FQuantumApiRequestOptions Options);
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"), Category = "Quantum API|Jobs")
    static UQuantumApiJsonAsyncAction* CancelJob(UObject* WorldContextObject, FString JobId, FQuantumApiRequestOptions Options);
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", WorldContext = "WorldContextObject"), Category = "Quantum API|Advanced")
    static UQuantumApiJsonAsyncAction* CallAdvancedJson(UObject* WorldContextObject, FQuantumApiAdvancedRequest Request, FQuantumApiRequestOptions Options);

    virtual void Activate() override;

private:
    enum class EActionKind : uint8 { EchoTypes, Circuit, Backends, Transpile, ImportQasm, ExportQasm, RunQasm, CircuitJob, QasmJob, RandomJob, JobStatus, JobResult, CancelJob, Advanced };
    static UQuantumApiJsonAsyncAction* Create(UObject* WorldContextObject, EActionKind Kind, FQuantumApiRequestOptions Options);

    EActionKind ActionKind = EActionKind::EchoTypes;
    FQuantumApiRequestOptions RequestOptions;
    FQuantumApiCircuitRunRequest CircuitRequest;
    FQuantumApiBackendListRequest BackendRequest;
    FQuantumApiTranspileRequest TranspileRequest;
    FQuantumApiQasmRequest QasmRequest;
    FQuantumApiCircuitDefinition ExportCircuit;
    FString ExportQasmVersion;
    FQuantumApiQasmRunRequest QasmRunRequest;
    FQuantumApiCircuitJobRequest CircuitJobRequest;
    FQuantumApiQasmJobRequest QasmJobRequest;
    FQuantumApiRandomJobRequest RandomJobRequest;
    FString JobId;
    FQuantumApiAdvancedRequest AdvancedRequest;
    TSharedPtr<class FQuantumApiClient> Client;
};
