using UnrealBuildTool;
using System.Collections.Generic;

public class QuantumApiDemoTarget : TargetRules
{
    public QuantumApiDemoTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V5;
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8;
        ExtraModuleNames.AddRange(new string[] { "QuantumApiDemo" });
    }
}
