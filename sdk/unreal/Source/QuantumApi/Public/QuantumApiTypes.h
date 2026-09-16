#pragma once

#include "CoreMinimal.h"
#include "QuantumApiTypes.generated.h"

UENUM(BlueprintType)
enum class EQuantumApiAuthMode : uint8
{
    BackendProxy UMETA(DisplayName = "Backend Proxy"),
    DirectApiKey UMETA(DisplayName = "Direct API Key (Development Only)")
};

/** The advanced endpoints deliberately exclude key and IBM credential lifecycle routes. */
UENUM(BlueprintType)
enum class EQuantumApiAdvancedEndpoint : uint8
{
    PortfolioMetadata UMETA(DisplayName = "Portfolio Metadata"),
    GroverSearch UMETA(DisplayName = "Algorithms: Grover Search"),
    AmplitudeEstimation UMETA(DisplayName = "Algorithms: Amplitude Estimation"),
    PhaseEstimation UMETA(DisplayName = "Algorithms: Phase Estimation"),
    TimeEvolution UMETA(DisplayName = "Algorithms: Time Evolution"),
    Qaoa UMETA(DisplayName = "Optimization: QAOA"),
    Vqe UMETA(DisplayName = "Optimization: VQE"),
    Maxcut UMETA(DisplayName = "Optimization: MaxCut"),
    Knapsack UMETA(DisplayName = "Optimization: Knapsack"),
    TravelingSalesperson UMETA(DisplayName = "Optimization: TSP"),
    StateTomography UMETA(DisplayName = "Experiments: State Tomography"),
    RandomizedBenchmarking UMETA(DisplayName = "Experiments: Randomized Benchmarking"),
    QuantumVolume UMETA(DisplayName = "Experiments: Quantum Volume"),
    T1 UMETA(DisplayName = "Experiments: T1"),
    T2Ramsey UMETA(DisplayName = "Experiments: T2 Ramsey"),
    PortfolioOptimization UMETA(DisplayName = "Finance: Portfolio Optimization"),
    PortfolioDiversification UMETA(DisplayName = "Finance: Portfolio Diversification"),
    KernelClassifier UMETA(DisplayName = "ML: Kernel Classifier"),
    VqcClassifier UMETA(DisplayName = "ML: VQC Classifier"),
    QsvrRegressor UMETA(DisplayName = "ML: QSVR Regressor"),
    GroundStateEnergy UMETA(DisplayName = "Nature: Ground State Energy"),
    FermionicMappingPreview UMETA(DisplayName = "Nature: Fermionic Mapping Preview")
};

USTRUCT(BlueprintType)
struct FQuantumApiRequestOptions
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API")
    FString OverrideApiKey;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API")
    FString OverrideBearerToken;

    /** Headers for the developer's proxy or custom auth scheme. They are never logged by this plugin. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API")
    TMap<FString, FString> ExtraHeaders;
};

USTRUCT(BlueprintType)
struct FQuantumApiResponseMeta
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    int32 StatusCode = 0;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    FString RequestId;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    TMap<FString, FString> Headers;
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
    bool bRetryable = false;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    float RetryAfterSeconds = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    TMap<FString, FString> Headers;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    FString RawBody;
};

USTRUCT(BlueprintType)
struct FQuantumApiJsonResponse
{
    GENERATED_BODY()

    /** Raw response JSON for rich domain endpoints. */
    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    FString Json;

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API")
    FQuantumApiResponseMeta Meta;
};

USTRUCT(BlueprintType)
struct FQuantumApiHealthResponse
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") FString Status;
    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") FString Service;
    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") FString Version;
    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") bool bQiskitAvailable = false;
    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") FString RuntimeMode;
    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") FQuantumApiResponseMeta Meta;
};

USTRUCT(BlueprintType)
struct FQuantumApiRunGateRequest
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString GateType = TEXT("bit_flip");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") bool bSendRotationAngle = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") double RotationAngleRad = 0.0;
};

USTRUCT(BlueprintType)
struct FQuantumApiRunGateResponse
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") FString GateType;
    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") int32 Measurement = 0;
    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") double SuperpositionStrength = 0.0;
    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") bool bSuccess = false;
    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") FQuantumApiResponseMeta Meta;
};

USTRUCT(BlueprintType)
struct FQuantumApiTextTransformRequest
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString Text;
};

USTRUCT(BlueprintType)
struct FQuantumApiTextTransformResponse
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") FString Original;
    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") FString Transformed;
    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") double CoveragePercent = 0.0;
    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") int32 QuantumWords = 0;
    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") int32 TotalWords = 0;
    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") TMap<FString, int32> CategoryCounts;
    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") FQuantumApiResponseMeta Meta;
};

USTRUCT(BlueprintType)
struct FQuantumApiRandomIntRequest
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") int32 Min = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") int32 Max = 1;
};

USTRUCT(BlueprintType)
struct FQuantumApiRandomIntResponse
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") int32 Value = 0;
    /** qiskit-simulator or classical-fallback. Neither is cryptographic randomness. */
    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") FString Source;
    UPROPERTY(BlueprintReadOnly, Category = "Quantum API") FQuantumApiResponseMeta Meta;
};

USTRUCT(BlueprintType)
struct FQuantumApiCircuitOperation
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString Gate = TEXT("h");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") int32 Target = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") bool bSendTheta = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") double Theta = 0.0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") bool bSendControl = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") int32 Control = 0;
};

USTRUCT(BlueprintType)
struct FQuantumApiCircuitDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") int32 NumQubits = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") TArray<FQuantumApiCircuitOperation> Operations;
};

USTRUCT(BlueprintType)
struct FQuantumApiCircuitRunRequest
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FQuantumApiCircuitDefinition Circuit;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") int32 Shots = 1024;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") bool bIncludeStatevector = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") bool bSendSeed = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") int32 Seed = 0;
};

USTRUCT(BlueprintType)
struct FQuantumApiBackendListRequest
{
    GENERATED_BODY()

    /** Empty, aer, or ibm. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString Provider;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") bool bSimulatorOnly = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API", meta = (ClampMin = "1")) int32 MinQubits = 1;
    /** Name only; the API resolves credentials for the key owner. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString IbmProfile;
};

USTRUCT(BlueprintType)
struct FQuantumApiTranspileRequest
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString BackendName;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString Provider;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString IbmProfile;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API", meta = (ClampMin = "0", ClampMax = "3")) int32 OptimizationLevel = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") bool bSendSeedTranspiler = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") int32 SeedTranspiler = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString OutputQasmVersion = TEXT("3");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") bool bUseQasmInput = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FQuantumApiCircuitDefinition Circuit;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API", meta = (EditCondition = "bUseQasmInput")) FString Qasm;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API", meta = (EditCondition = "bUseQasmInput")) FString QasmVersion = TEXT("auto");
};

USTRUCT(BlueprintType)
struct FQuantumApiQasmRequest
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString Qasm;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString QasmVersion = TEXT("auto");
};

USTRUCT(BlueprintType)
struct FQuantumApiQasmRunRequest
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString Qasm;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString QasmVersion = TEXT("auto");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") bool bUseAnalyticMode = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API", meta = (EditCondition = "!bUseAnalyticMode")) int32 Shots = 1024;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") bool bIncludeStatevector = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") bool bSendSeed = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") int32 Seed = 0;
};

USTRUCT(BlueprintType)
struct FQuantumApiCircuitJobRequest
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString BackendName;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString IbmProfile;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FQuantumApiCircuitDefinition Circuit;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") int32 Shots = 1024;
};

USTRUCT(BlueprintType)
struct FQuantumApiQasmJobRequest
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString BackendName;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString IbmProfile;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString Qasm;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString QasmVersion = TEXT("auto");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") int32 Shots = 1024;
};

USTRUCT(BlueprintType)
struct FQuantumApiRandomJobRequest
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString BackendName;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString IbmProfile;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") int32 Min = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") int32 Max = 1;
};

USTRUCT(BlueprintType)
struct FQuantumApiAdvancedRequest
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") EQuantumApiAdvancedEndpoint Endpoint = EQuantumApiAdvancedEndpoint::PortfolioMetadata;
    /** JSON body for POST routes. Leave empty for Portfolio Metadata. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") FString JsonBody;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum API") TMap<FString, FString> QueryParameters;
};
