// Copyright (c) 2026 David J. Grimsley. All rights reserved.
using UnrealBuildTool;

public class QuantumApiDemo : ModuleRules
{
    public QuantumApiDemo(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "InputCore", "QuantumApi" });
    }
}
