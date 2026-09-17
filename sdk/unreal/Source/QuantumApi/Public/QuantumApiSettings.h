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
    /** Hidden from Project Settings; advanced/self-hosted users can still override it in DefaultGame.ini. */
    UPROPERTY(Config)
    FString BaseUrl = TEXT("https://davidjgrimsley.com/public-facing/api/quantum/v1");

    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API")
    EQuantumApiAuthMode AuthMode = EQuantumApiAuthMode::BackendProxy;

    /**
     * Sent only in DirectApiKey mode. Packaged client configuration is not a secret store;
     * prefer BackendProxy for a shipping game.
     */
    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API")
    FString ApiKey;

    /**
     * In DirectApiKey mode, prefer a developer-machine environment variable over the
     * value above. This is convenient for local editor work, but is not a secret store
     * for a packaged game; use BackendProxy for shipping clients.
     */
    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API|Local Development")
    bool bUseEnvironmentApiKey = true;

    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API|Local Development", meta = (EditCondition = "bUseEnvironmentApiKey"))
    FString ApiKeyEnvironmentVariable = TEXT("QUANTUM_API_KEY");

    /** Optional bearer token for the developer's proxy or authenticated API flow. */
    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API")
    FString BearerToken;

    /**
     * Optional non-secret IBM profile name used by IBM backend, transpile, and job
     * requests when the Blueprint request leaves IbmProfile blank. IBM credentials
     * are still created and stored on the Quantum API service, not in the game.
     */
    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API|IBM Hardware", meta = (DisplayName = "Default IBM Profile Name"))
    FString DefaultIbmProfile;

    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API", meta = (ClampMin = "1.0"))
    float RequestTimeoutSeconds = 10.0f;

    /** GET-only retries for transport, 429, 502, 503, and 504 failures. POSTs are never retried. */
    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API|Reliability", meta = (ClampMin = "0", ClampMax = "2"))
    int32 MaxReadRetries = 2;

    /** Caps Retry-After delays so a gameplay action cannot wait indefinitely. */
    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API|Reliability", meta = (ClampMin = "0.1", ClampMax = "10.0"))
    float MaxRetryDelaySeconds = 5.0f;

    UFUNCTION(BlueprintPure, Category = "Quantum API")
    FString GetNormalizedBaseUrl() const;

    /** Resolves the local-only environment override before falling back to ApiKey. */
    UFUNCTION(BlueprintPure, Category = "Quantum API|Local Development")
    FString GetResolvedApiKey() const;

    /** Returns the optional non-secret IBM profile fallback with editor whitespace removed. */
    UFUNCTION(BlueprintPure, Category = "Quantum API|IBM Hardware")
    FString GetDefaultIbmProfile() const;
};
