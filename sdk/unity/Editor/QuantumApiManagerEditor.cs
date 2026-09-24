using QuantumApi.Unity;
using UnityEditor;

namespace QuantumApi.Unity.Editor
{
    [CustomEditor(typeof(QuantumApiManager))]
    public sealed class QuantumApiManagerEditor : UnityEditor.Editor
    {
        public override void OnInspectorGUI()
        {
            serializedObject.Update();
            var proxyMode = serializedObject.FindProperty("backendProxyMode");
            EditorGUILayout.PropertyField(proxyMode, new UnityEngine.GUIContent("Backend Proxy Mode"));
            EditorGUILayout.PropertyField(
                serializedObject.FindProperty(proxyMode.boolValue ? "backendProxyUrl" : "apiKey"),
                new UnityEngine.GUIContent(proxyMode.boolValue ? "Backend Proxy URL" : "API Key (Direct Mode)"));
            EditorGUILayout.PropertyField(serializedObject.FindProperty("timeoutSeconds"));
            EditorGUILayout.Space();
            EditorGUILayout.LabelField("IBM Hardware Defaults", EditorStyles.boldLabel);
            EditorGUILayout.PropertyField(serializedObject.FindProperty("defaultIbmBackend"));
            EditorGUILayout.PropertyField(serializedObject.FindProperty("defaultIbmProfile"));
            serializedObject.ApplyModifiedProperties();
        }
    }
}
