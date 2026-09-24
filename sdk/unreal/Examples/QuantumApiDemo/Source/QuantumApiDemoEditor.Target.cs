// Copyright (c) 2026 David J. Grimsley. All rights reserved.
using UnrealBuildTool;
using System.Collections.Generic;

public class QuantumApiDemoEditorTarget : TargetRules
{
    public QuantumApiDemoEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V7;
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8;
        ExtraModuleNames.AddRange(new string[] { "QuantumApiDemo" });
    }
}
