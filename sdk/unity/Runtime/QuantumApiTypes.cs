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
        [NonSerialized]
        public bool sendRotationAngle;
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
    public sealed class RandomIntRequest
    {
        public int min;
        public int max;
    }

    [Serializable]
    public sealed class RandomIntResponse
    {
        public int value;
        public string source = "";
    }

    [Serializable]
    public sealed class RandomJobSubmitRequest
    {
        public int min;
        public int max;
        public string provider = "ibm";
        public string backend_name = "";
        public string ibm_profile = "";
    }

    [Serializable]
    public sealed class RandomJobSubmitResponse
    {
        public string job_id = "";
        public string provider = "";
        public string backend_name = "";
        public string ibm_profile = "";
        public string remote_job_id = "";
        public string status = "";
        public string created_at = "";
    }

    [Serializable]
    public sealed class RandomJobStatusResponse
    {
        public string job_id = "";
        public string provider = "";
        public string backend_name = "";
        public string ibm_profile = "";
        public string remote_job_id = "";
        public string status = "";
        public string created_at = "";
        public string updated_at = "";
        public string completed_at = "";
        public RandomJobError error;
    }

    [Serializable]
    public sealed class RandomJobResultResponse
    {
        public string job_id = "";
        public string status = "";
        public RandomJobResultData result = new RandomJobResultData();
    }

    [Serializable]
    public sealed class RandomJobResultData
    {
        public int value;
        public string source = "";
    }

    [Serializable]
    public sealed class RandomJobError
    {
        public string error = "";
        public string message = "";
        public string request_id = "";
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
