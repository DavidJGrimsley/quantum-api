// Copyright (c) 2026 David J. Grimsley. All rights reserved.
#pragma once

#include "Modules/ModuleManager.h"

class FQuantumApiModule final : public IModuleInterface
{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;
};
