// Copyright (c) 2026 David J. Grimsley. All rights reserved.
using UnrealBuildTool;

public class QuantumApi : ModuleRules
{
    public QuantumApi(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PrecompileForTargets = PrecompileTargetsType.Any;

        PublicDependencyModuleNames.AddRange(
            new[]
            {
                "Core",
                "CoreUObject",
                "Engine",
                "HTTP",
                "Json",
                "JsonUtilities",
                "DeveloperSettings"
            }
        );
    }
}
