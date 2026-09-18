@tool
extends EditorPlugin

const ProjectSettingsHelper = preload("res://addons/quantum_api_client/project_settings.gd")

func _enter_tree() -> void:
	ProjectSettingsHelper.register()
