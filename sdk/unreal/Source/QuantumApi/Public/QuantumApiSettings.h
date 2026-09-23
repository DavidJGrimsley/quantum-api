// Copyright (c) 2026 David J. Grimsley. All rights reserved.
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
    EQuantumApiAuthMode AuthMode = EQuantumApiAuthMode::DirectApiKey;

    /**
     * Sent only in DirectApiKey mode. Packaged client configuration is not a secret store;
     * prefer BackendProxy for a shipping game.
     */
    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API", meta = (EditCondition = "AuthMode == EQuantumApiAuthMode::DirectApiKey", EditConditionHides, PasswordField = true))
    FString ApiKey;

    /**
     * Required only in BackendProxy mode. The proxy must expose the compatible Quantum
     * API /v1 contract and keep the upstream API key on the server.
     */
    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API", meta = (DisplayName = "Backend Proxy URL", EditCondition = "AuthMode == EQuantumApiAuthMode::BackendProxy", EditConditionHides))
    FString BackendProxyUrl;

    /**
     * Optional non-secret IBM profile name used by IBM backend, transpile, and job
     * requests when the Blueprint request leaves IbmProfile blank. IBM credentials
     * are still created and stored on the Quantum API service, not in the game.
     */
    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API|IBM Hardware", meta = (DisplayName = "Default IBM Profile Name"))
    FString DefaultIbmProfile;

    /**
     * Optional IBM backend fallback for job and transpile requests. An explicit
     * BackendName on a request always takes priority over this setting.
     */
    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API|IBM Hardware", meta = (DisplayName = "Default IBM Hardware Backend"))
    FString DefaultIbmHardwareBackend;

    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API", meta = (ClampMin = "1.0"))
    float RequestTimeoutSeconds = 10.0f;

    /** GET-only retries for transport, 429, 502, 503, and 504 failures. POSTs are never retried. */
    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API|Reliability", meta = (ClampMin = "0", ClampMax = "2"))
    int32 MaxReadRetries = 2;

    /** Caps Retry-After delays so a gameplay action cannot wait indefinitely. */
    UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Quantum API|Reliability", meta = (ClampMin = "0.1", ClampMax = "10.0"))
    float MaxRetryDelaySeconds = 5.0f;

    /** Returns the hosted API URL for Direct mode or the normalized custom proxy URL. */
    FString GetResolvedBaseUrl() const;

    /** Returns the optional non-secret IBM profile fallback with editor whitespace removed. */
    UFUNCTION(BlueprintPure, Category = "Quantum API|IBM Hardware")
    FString GetDefaultIbmProfile() const;

    /** Returns the optional IBM hardware-backend fallback with editor whitespace removed. */
    UFUNCTION(BlueprintPure, Category = "Quantum API|IBM Hardware")
    FString GetDefaultIbmHardwareBackend() const;
};
