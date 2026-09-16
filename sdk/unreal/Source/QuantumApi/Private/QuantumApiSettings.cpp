#include "QuantumApiSettings.h"

#include "HAL/PlatformMisc.h"

FString UQuantumApiSettings::GetNormalizedBaseUrl() const
{
    FString Normalized = BaseUrl;
    while (Normalized.EndsWith(TEXT("/")))
    {
        Normalized.LeftChopInline(1);
    }
    if (!Normalized.EndsWith(TEXT("/v1")))
    {
        Normalized += TEXT("/v1");
    }
    return Normalized;
}

FString UQuantumApiSettings::GetResolvedApiKey() const
{
    if (bUseEnvironmentApiKey && !ApiKeyEnvironmentVariable.IsEmpty())
    {
        const FString EnvironmentValue = FPlatformMisc::GetEnvironmentVariable(*ApiKeyEnvironmentVariable);
        if (!EnvironmentValue.IsEmpty())
        {
            return EnvironmentValue;
        }
    }
    return ApiKey;
}

FString UQuantumApiSettings::GetDefaultIbmProfile() const
{
    FString Profile = DefaultIbmProfile;
    Profile.TrimStartAndEndInline();
    return Profile;
}
