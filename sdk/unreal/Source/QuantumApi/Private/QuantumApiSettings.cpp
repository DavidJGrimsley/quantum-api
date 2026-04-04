#include "QuantumApiSettings.h"

FString UQuantumApiSettings::GetNormalizedBaseUrl() const
{
    FString Normalized = BaseUrl;
    while (Normalized.EndsWith(TEXT("/")))
    {
        Normalized.LeftChopInline(1, false);
    }
    if (!Normalized.EndsWith(TEXT("/v1")))
    {
        Normalized += TEXT("/v1");
    }
    return Normalized;
}
