#include "QuantumApiSettings.h"

FString UQuantumApiSettings::GetNormalizedBaseUrl() const
{
    FString Normalized = BaseUrl;
    while (Normalized.EndsWith(TEXT("/")))
    {
        Normalized.LeftChopInline(1, false);
    }
    return Normalized;
}
