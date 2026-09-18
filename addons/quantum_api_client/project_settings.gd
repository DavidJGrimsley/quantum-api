@tool
class_name QuantumApiProjectSettings
extends RefCounted

## Registers the Quantum API runtime settings with Godot's Project Settings UI.
##
## The client can always read values written directly into project.godot. This
## helper exists so a beginner can discover and edit those values in the editor
## without having to know the setting paths in advance.

# Godot's Basic Project Settings view hides an unchanged empty custom string in
# some editor versions. A non-empty editor-only initial value keeps the actual
# setting visible while the runtime client maps it back to an empty profile.
const ACCOUNT_DEFAULT_PROFILE_INITIAL_VALUE := "__quantum_api_use_account_default__"

const SETTINGS := [
	{
		"name": "quantum_api/base_url",
		"default": "https://davidjgrimsley.com/public-facing/api/quantum/v1",
		"type": TYPE_STRING,
		"hint": PROPERTY_HINT_NONE,
		"hint_string": "",
	},
	{
		"name": "quantum_api/backend_proxy_mode",
		"default": true,
		"type": TYPE_BOOL,
		"hint": PROPERTY_HINT_NONE,
		"hint_string": "",
	},
	{
		"name": "quantum_api/direct_api_key",
		"default": "",
		"type": TYPE_STRING,
		"hint": PROPERTY_HINT_PASSWORD,
		"hint_string": "",
	},
	{
		"name": "quantum_api/default_ibm_profile",
		"default": "",
		"initial": ACCOUNT_DEFAULT_PROFILE_INITIAL_VALUE,
		"type": TYPE_STRING,
		"hint": PROPERTY_HINT_NONE,
		"hint_string": "",
	},
	{
		"name": "quantum_api/request_timeout_seconds",
		"default": 10.0,
		"type": TYPE_FLOAT,
		"hint": PROPERTY_HINT_RANGE,
		"hint_string": "0.1,120.0,0.1,or_greater",
	},
]

static func register() -> void:
	for setting_info in SETTINGS:
		var setting_name := str(setting_info["name"])
		var default_value: Variant = setting_info["default"]
		var initial_value: Variant = setting_info.get("initial", default_value)
		if !ProjectSettings.has_setting(setting_name):
			ProjectSettings.set_setting(setting_name, default_value)
		ProjectSettings.set_initial_value(setting_name, initial_value)
		ProjectSettings.set_as_basic(setting_name, true)
		ProjectSettings.add_property_info(setting_info)
