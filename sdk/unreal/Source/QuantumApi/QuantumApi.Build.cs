using UnrealBuildTool;

public class QuantumApi : ModuleRules
{
    public QuantumApi(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

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
