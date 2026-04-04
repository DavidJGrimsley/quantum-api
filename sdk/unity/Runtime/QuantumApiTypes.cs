using System;
using System.Collections.Generic;

namespace QuantumApi.Unity
{
    public enum QuantumApiAuthMode
    {
        Auto,
        ApiKey,
        Bearer,
        None,
    }

    [Serializable]
    public sealed class QuantumApiClientOptions
    {
        public string BaseUrl = "";
        public bool BackendProxyMode = true;
        public string ApiKey = "";
        public string BearerToken = "";
        public QuantumApiAuthMode DefaultAuthMode = QuantumApiAuthMode.Auto;
        public int TimeoutSeconds = 15;
    }

    public sealed class QuantumApiRequestOptions
    {
        public QuantumApiAuthMode AuthMode = QuantumApiAuthMode.Auto;
        public string ApiKey;
        public string BearerToken;
        public Dictionary<string, string> Headers;
        public int? TimeoutSeconds;
    }

    [Serializable]
    public sealed class HealthResponse
    {
        public string status = "";
        public string service = "";
        public string version = "";
        public bool qiskit_available;
        public string runtime_mode = "";
    }

    [Serializable]
    public sealed class EchoTypeInfo
    {
        public string name = "";
        public string description = "";
    }

    [Serializable]
    public sealed class EchoTypesResponse
    {
        public EchoTypeInfo[] echo_types = Array.Empty<EchoTypeInfo>();
    }

    [Serializable]
    public sealed class GateRunRequest
    {
        public string gate_type = "";
        public float rotation_angle_rad;
    }

    [Serializable]
    public sealed class GateRunResponse
    {
        public string gate_type = "";
        public int measurement;
        public float superposition_strength;
        public bool success;
    }

    [Serializable]
    public sealed class TextTransformRequest
    {
        public string text = "";
    }

    [Serializable]
    public sealed class CategoryCountEntry
    {
        public string category = "";
        public int count;
    }

    [Serializable]
    public sealed class TextTransformResponse
    {
        public string original = "";
        public string transformed = "";
        public float coverage_percent;
        public int quantum_words;
        public int total_words;

        [NonSerialized]
        public List<CategoryCountEntry> category_counts = new List<CategoryCountEntry>();

        [NonSerialized]
        public string raw_category_counts_json = "{}";
    }

    [Serializable]
    internal sealed class QuantumApiErrorEnvelope
    {
        public string error = "";
        public string message = "";
        public string request_id = "";
    }
}
