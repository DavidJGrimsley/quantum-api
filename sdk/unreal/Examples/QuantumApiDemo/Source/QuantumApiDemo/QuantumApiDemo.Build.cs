using UnrealBuildTool;

public class QuantumApiDemo : ModuleRules
{
    public QuantumApiDemo(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "InputCore", "QuantumApi" });
    }
}
