#include "QuantumApiSettings.h"

namespace
{
constexpr const TCHAR* HostedQuantumApiBaseUrl = TEXT("https://davidjgrimsley.com/public-facing/api/quantum/v1");

FString NormalizeMountedV1Url(FString Url)
{
    Url.TrimStartAndEndInline();
    while (Url.EndsWith(TEXT("/")))
    {
        Url.LeftChopInline(1);
    }
    if (!Url.IsEmpty() && !Url.EndsWith(TEXT("/v1"), ESearchCase::IgnoreCase))
    {
        Url += TEXT("/v1");
    }
    return Url;
}
}

FString UQuantumApiSettings::GetResolvedBaseUrl() const
{
    return AuthMode == EQuantumApiAuthMode::DirectApiKey
        ? FString(HostedQuantumApiBaseUrl)
        : NormalizeMountedV1Url(BackendProxyUrl);
}

FString UQuantumApiSettings::GetDefaultIbmProfile() const
{
    FString Profile = DefaultIbmProfile;
    Profile.TrimStartAndEndInline();
    return Profile;
}

FString UQuantumApiSettings::GetDefaultIbmHardwareBackend() const
{
    FString Backend = DefaultIbmHardwareBackend;
    Backend.TrimStartAndEndInline();
    return Backend;
}
