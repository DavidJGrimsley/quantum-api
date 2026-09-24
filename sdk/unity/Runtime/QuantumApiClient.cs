// Copyright (c) 2026 David J. Grimsley. All rights reserved.
using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;
using UnityEngine.Networking;

namespace QuantumApi.Unity
{
    public sealed class QuantumApiClient
    {
        private const string BaseUrl = "https://davidjgrimsley.com/public-facing/api/quantum/v1";
        private readonly string _apiKey;
        private readonly bool _backendProxyMode;
        private readonly string _baseUrl;
        private readonly string _defaultIbmBackend;
        private readonly string _defaultIbmProfile;
        private readonly string _bearerToken;
        private readonly QuantumApiAuthMode _defaultAuthMode;
        private readonly int _timeoutSeconds;

        public QuantumApiClient(QuantumApiClientOptions options)
        {
            if (options == null)
            {
                throw new ArgumentNullException(nameof(options));
            }

            _apiKey = (options.ApiKey ?? string.Empty).Trim();
            _backendProxyMode = options.BackendProxyMode;
            _baseUrl = _backendProxyMode ? NormalizeProxyUrl(options.BackendProxyUrl) : BaseUrl;
            _defaultIbmBackend = (options.DefaultIbmBackend ?? string.Empty).Trim();
            _defaultIbmProfile = (options.DefaultIbmProfile ?? string.Empty).Trim();
            _bearerToken = (options.BearerToken ?? string.Empty).Trim();
            _defaultAuthMode = options.DefaultAuthMode;
            _timeoutSeconds = options.TimeoutSeconds > 0 ? options.TimeoutSeconds : 15;
        }

        public Task<HealthResponse> HealthAsync(QuantumApiRequestOptions requestOptions = null)
        {
            return SendAsync<HealthResponse>("/health", UnityWebRequest.kHttpVerbGET, null, requestOptions);
        }

        public Task<EchoTypesResponse> GetEchoTypesAsync(QuantumApiRequestOptions requestOptions = null)
        {
            return SendAsync<EchoTypesResponse>("/echo-types", UnityWebRequest.kHttpVerbGET, null, requestOptions);
        }

        public Task<GateRunResponse> RunGateAsync(GateRunRequest request, QuantumApiRequestOptions requestOptions = null)
        {
            if (request == null)
            {
                return FailTask<GateRunResponse>("invalid_request", "Quantum API gate execution requires a payload.");
            }

            return SendAsync<GateRunResponse>("/gates/run", UnityWebRequest.kHttpVerbPOST, BuildGateRunJson(request), requestOptions);
        }

        public Task<RandomIntResponse> RandomIntAsync(
            int min,
            int max,
            QuantumApiRequestOptions requestOptions = null)
        {
            return SendAsync<RandomIntResponse>(
                "/random",
                UnityWebRequest.kHttpVerbPOST,
                new RandomIntRequest { min = min, max = max },
                requestOptions);
        }

        public Task<RandomJobSubmitResponse> SubmitRandomJobAsync(
            RandomJobSubmitRequest request,
            QuantumApiRequestOptions requestOptions = null)
        {
            if (request == null)
            {
                return FailTask<RandomJobSubmitResponse>("invalid_request", "Quantum API random hardware job submission requires a payload.");
            }

            return SendAsync<RandomJobSubmitResponse>(
                "/jobs/random",
                UnityWebRequest.kHttpVerbPOST,
                BuildRandomJobSubmitJson(request),
                requestOptions);
        }

        public Task<RandomJobStatusResponse> GetJobAsync(
            string jobId,
            QuantumApiRequestOptions requestOptions = null)
        {
            if (string.IsNullOrWhiteSpace(jobId))
            {
                return FailTask<RandomJobStatusResponse>("invalid_request", "Quantum API job status requires a job id.");
            }

            return SendAsync<RandomJobStatusResponse>(
                $"/jobs/{EscapePathSegment(jobId)}",
                UnityWebRequest.kHttpVerbGET,
                null,
                requestOptions);
        }

        public Task<RandomJobResultResponse> GetJobResultAsync(
            string jobId,
            QuantumApiRequestOptions requestOptions = null)
        {
            if (string.IsNullOrWhiteSpace(jobId))
            {
                return FailTask<RandomJobResultResponse>("invalid_request", "Quantum API job result requires a job id.");
            }

            return SendAsync<RandomJobResultResponse>(
                $"/jobs/{EscapePathSegment(jobId)}/result",
                UnityWebRequest.kHttpVerbGET,
                null,
                requestOptions);
        }

        public Task<RandomJobStatusResponse> CancelJobAsync(
            string jobId,
            QuantumApiRequestOptions requestOptions = null)
        {
            if (string.IsNullOrWhiteSpace(jobId))
            {
                return FailTask<RandomJobStatusResponse>("invalid_request", "Quantum API job cancellation requires a job id.");
            }

            return SendAsync<RandomJobStatusResponse>(
                $"/jobs/{EscapePathSegment(jobId)}/cancel",
                UnityWebRequest.kHttpVerbPOST,
                null,
                requestOptions);
        }

        public Task<TextTransformResponse> TransformTextAsync(
            TextTransformRequest request,
            QuantumApiRequestOptions requestOptions = null)
        {
            if (request == null)
            {
                return FailTask<TextTransformResponse>("invalid_request", "Quantum API text transform requires a payload.");
            }

            return SendAsync<TextTransformResponse>("/text/transform", UnityWebRequest.kHttpVerbPOST, request, requestOptions);
        }

        public async Task<TextTransformResponse> TransformTextWithFallbackAsync(
            TextTransformRequest request,
            string fallbackText = null,
            QuantumApiRequestOptions requestOptions = null)
        {
            if (request == null)
            {
                throw QuantumApiError.Local("invalid_request", "Quantum API text transform requires a payload.");
            }

            try
            {
                return await TransformTextAsync(request, requestOptions).ConfigureAwait(false);
            }
            catch (QuantumApiError)
            {
                return CreateTextTransformFallback(request.text, fallbackText);
            }
        }

        public IEnumerator HealthCoroutine(
            Action<HealthResponse> onSuccess,
            Action<QuantumApiError> onError,
            QuantumApiRequestOptions requestOptions = null)
        {
            return SendCoroutine("/health", UnityWebRequest.kHttpVerbGET, null, onSuccess, onError, requestOptions);
        }

        public IEnumerator GetEchoTypesCoroutine(
            Action<EchoTypesResponse> onSuccess,
            Action<QuantumApiError> onError,
            QuantumApiRequestOptions requestOptions = null)
        {
            return SendCoroutine("/echo-types", UnityWebRequest.kHttpVerbGET, null, onSuccess, onError, requestOptions);
        }

        public IEnumerator RunGateCoroutine(
            GateRunRequest request,
            Action<GateRunResponse> onSuccess,
            Action<QuantumApiError> onError,
            QuantumApiRequestOptions requestOptions = null)
        {
            if (request == null)
            {
                onError?.Invoke(QuantumApiError.Local("invalid_request", "Quantum API gate execution requires a payload."));
                yield break;
            }

            yield return SendCoroutine("/gates/run", UnityWebRequest.kHttpVerbPOST, BuildGateRunJson(request), onSuccess, onError, requestOptions);
        }

        public IEnumerator RandomIntCoroutine(
            int min,
            int max,
            Action<RandomIntResponse> onSuccess,
            Action<QuantumApiError> onError,
            QuantumApiRequestOptions requestOptions = null)
        {
            yield return SendCoroutine(
                "/random",
                UnityWebRequest.kHttpVerbPOST,
                new RandomIntRequest { min = min, max = max },
                onSuccess,
                onError,
                requestOptions);
        }

        public IEnumerator SubmitRandomJobCoroutine(
            RandomJobSubmitRequest request,
            Action<RandomJobSubmitResponse> onSuccess,
            Action<QuantumApiError> onError,
            QuantumApiRequestOptions requestOptions = null)
        {
            if (request == null)
            {
                onError?.Invoke(QuantumApiError.Local("invalid_request", "Quantum API random hardware job submission requires a payload."));
                yield break;
            }

            yield return SendCoroutine(
                "/jobs/random",
                UnityWebRequest.kHttpVerbPOST,
                BuildRandomJobSubmitJson(request),
                onSuccess,
                onError,
                requestOptions);
        }

        public IEnumerator GetJobCoroutine(
            string jobId,
            Action<RandomJobStatusResponse> onSuccess,
            Action<QuantumApiError> onError,
            QuantumApiRequestOptions requestOptions = null)
        {
            if (string.IsNullOrWhiteSpace(jobId))
            {
                onError?.Invoke(QuantumApiError.Local("invalid_request", "Quantum API job status requires a job id."));
                yield break;
            }

            yield return SendCoroutine(
                $"/jobs/{EscapePathSegment(jobId)}",
                UnityWebRequest.kHttpVerbGET,
                null,
                onSuccess,
                onError,
                requestOptions);
        }

        public IEnumerator GetJobResultCoroutine(
            string jobId,
            Action<RandomJobResultResponse> onSuccess,
            Action<QuantumApiError> onError,
            QuantumApiRequestOptions requestOptions = null)
        {
            if (string.IsNullOrWhiteSpace(jobId))
            {
                onError?.Invoke(QuantumApiError.Local("invalid_request", "Quantum API job result requires a job id."));
                yield break;
            }

            yield return SendCoroutine(
                $"/jobs/{EscapePathSegment(jobId)}/result",
                UnityWebRequest.kHttpVerbGET,
                null,
                onSuccess,
                onError,
                requestOptions);
        }

        public IEnumerator CancelJobCoroutine(
            string jobId,
            Action<RandomJobStatusResponse> onSuccess,
            Action<QuantumApiError> onError,
            QuantumApiRequestOptions requestOptions = null)
        {
            if (string.IsNullOrWhiteSpace(jobId))
            {
                onError?.Invoke(QuantumApiError.Local("invalid_request", "Quantum API job cancellation requires a job id."));
                yield break;
            }

            yield return SendCoroutine(
                $"/jobs/{EscapePathSegment(jobId)}/cancel",
                UnityWebRequest.kHttpVerbPOST,
                null,
                onSuccess,
                onError,
                requestOptions);
        }

        public IEnumerator TransformTextCoroutine(
            TextTransformRequest request,
            Action<TextTransformResponse> onSuccess,
            Action<QuantumApiError> onError,
            QuantumApiRequestOptions requestOptions = null)
        {
            if (request == null)
            {
                onError?.Invoke(QuantumApiError.Local("invalid_request", "Quantum API text transform requires a payload."));
                yield break;
            }

            yield return SendCoroutine("/text/transform", UnityWebRequest.kHttpVerbPOST, request, onSuccess, onError, requestOptions);
        }

        public IEnumerator TransformTextWithFallbackCoroutine(
            TextTransformRequest request,
            Action<TextTransformResponse> onComplete,
            string fallbackText = null,
            Action<QuantumApiError> onError = null,
            QuantumApiRequestOptions requestOptions = null)
        {
            if (request == null)
            {
                onError?.Invoke(QuantumApiError.Local("invalid_request", "Quantum API text transform requires a payload."));
                yield break;
            }

            yield return TransformTextCoroutine(
                request,
                response => onComplete?.Invoke(response),
                error =>
                {
                    onError?.Invoke(error);
                    onComplete?.Invoke(CreateTextTransformFallback(request.text, fallbackText));
                },
                requestOptions);
        }

        public static TextTransformResponse CreateTextTransformFallback(string originalText, string fallbackText = null)
        {
            var original = originalText ?? string.Empty;
            var transformed = string.IsNullOrWhiteSpace(fallbackText) ? original : fallbackText;

            return new TextTransformResponse
            {
                original = original,
                transformed = transformed,
                coverage_percent = 0f,
                quantum_words = 0,
                total_words = CountWords(original),
                category_counts = new List<CategoryCountEntry>(),
                raw_category_counts_json = "{}",
            };
        }

        private Task<T> SendAsync<T>(
            string path,
            string method,
            object body,
            QuantumApiRequestOptions requestOptions)
            where T : class, new()
        {
            var request = BuildRequest(path, method, body, requestOptions, out var configurationError);
            if (configurationError != null)
            {
                return FailTask<T>(configurationError);
            }

            var completionSource = new TaskCompletionSource<T>();
            var operation = request.SendWebRequest();
            operation.completed += _ =>
            {
                try
                {
                    if (IsSuccessStatusCode(request.responseCode))
                    {
                        completionSource.TrySetResult(ParseResponse<T>(request.downloadHandler != null ? request.downloadHandler.text : string.Empty));
                        return;
                    }

                    if (request.responseCode > 0)
                    {
                        completionSource.TrySetException(QuantumApiError.FromResponse(
                            request.responseCode,
                            request.downloadHandler != null ? request.downloadHandler.text : string.Empty,
                            request.GetResponseHeaders()));
                        return;
                    }

                    completionSource.TrySetException(QuantumApiError.Local(
                        "request_failed",
                        request.error ?? "Quantum API request failed before receiving an HTTP response."));
                }
                finally
                {
                    request.Dispose();
                }
            };

            return completionSource.Task;
        }

        private IEnumerator SendCoroutine<T>(
            string path,
            string method,
            object body,
            Action<T> onSuccess,
            Action<QuantumApiError> onError,
            QuantumApiRequestOptions requestOptions)
            where T : class, new()
        {
            var request = BuildRequest(path, method, body, requestOptions, out var configurationError);
            if (configurationError != null)
            {
                onError?.Invoke(configurationError);
                yield break;
            }

            var operation = request.SendWebRequest();
            yield return operation;

            try
            {
                if (IsSuccessStatusCode(request.responseCode))
                {
                    onSuccess?.Invoke(ParseResponse<T>(request.downloadHandler != null ? request.downloadHandler.text : string.Empty));
                    yield break;
                }

                if (request.responseCode > 0)
                {
                    onError?.Invoke(QuantumApiError.FromResponse(
                        request.responseCode,
                        request.downloadHandler != null ? request.downloadHandler.text : string.Empty,
                        request.GetResponseHeaders()));
                    yield break;
                }

                onError?.Invoke(QuantumApiError.Local(
                    "request_failed",
                    request.error ?? "Quantum API request failed before receiving an HTTP response."));
            }
            finally
            {
                request.Dispose();
            }
        }

        private UnityWebRequest BuildRequest(
            string path,
            string method,
            object body,
            QuantumApiRequestOptions requestOptions,
            out QuantumApiError configurationError)
        {
            configurationError = null;
            var resolvedAuthMode = ResolveAuthMode(path, requestOptions != null ? requestOptions.AuthMode : _defaultAuthMode);
            var apiKey = requestOptions != null && !string.IsNullOrWhiteSpace(requestOptions.ApiKey)
                ? requestOptions.ApiKey.Trim()
                : _apiKey;
            var bearerToken = requestOptions != null && !string.IsNullOrWhiteSpace(requestOptions.BearerToken)
                ? requestOptions.BearerToken.Trim()
                : _bearerToken;

            if (_backendProxyMode && string.IsNullOrEmpty(_baseUrl))
            {
                configurationError = QuantumApiError.Local("missing_proxy_url", "Backend proxy mode requires a valid HTTP or HTTPS URL.");
                return null;
            }

            if (!_backendProxyMode && resolvedAuthMode == QuantumApiAuthMode.ApiKey && string.IsNullOrWhiteSpace(apiKey))
            {
                configurationError = QuantumApiError.Local(
                    "missing_api_key",
                    $"Quantum API request to {path} requires an API key.");
                return null;
            }

            if (!_backendProxyMode && resolvedAuthMode == QuantumApiAuthMode.Bearer && string.IsNullOrWhiteSpace(bearerToken))
            {
                configurationError = QuantumApiError.Local(
                    "missing_bearer_token",
                    $"Quantum API request to {path} requires a bearer token.");
                return null;
            }

            var request = new UnityWebRequest(_baseUrl + path, method)
            {
                downloadHandler = new DownloadHandlerBuffer(),
                timeout = requestOptions != null && requestOptions.TimeoutSeconds.HasValue && requestOptions.TimeoutSeconds.Value > 0
                    ? requestOptions.TimeoutSeconds.Value
                    : _timeoutSeconds,
            };

            if (requestOptions != null && requestOptions.Headers != null)
            {
                foreach (var pair in requestOptions.Headers)
                {
                    if (!_backendProxyMode || (!string.Equals(pair.Key, "X-API-Key", StringComparison.OrdinalIgnoreCase)
                        && !string.Equals(pair.Key, "Authorization", StringComparison.OrdinalIgnoreCase)))
                    {
                        request.SetRequestHeader(pair.Key, pair.Value);
                    }
                }
            }

            request.SetRequestHeader("Accept", "application/json");

            if (body != null)
            {
                var payloadJson = QuantumApiJson.Serialize(body);
                request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(payloadJson));
                request.SetRequestHeader("Content-Type", "application/json");
            }

            if (!_backendProxyMode && resolvedAuthMode == QuantumApiAuthMode.ApiKey)
            {
                request.SetRequestHeader("X-API-Key", apiKey);
            }
            else if (!_backendProxyMode && resolvedAuthMode == QuantumApiAuthMode.Bearer)
            {
                request.SetRequestHeader("Authorization", $"Bearer {bearerToken}");
            }

            return request;
        }

        private QuantumApiAuthMode ResolveAuthMode(string path, QuantumApiAuthMode requested)
        {
            if (requested != QuantumApiAuthMode.Auto)
            {
                return requested;
            }

            if (path == "/health" || path == "/portfolio.json")
            {
                return QuantumApiAuthMode.None;
            }

            if (path.StartsWith("/keys", StringComparison.Ordinal) || path.StartsWith("/ibm/profiles", StringComparison.Ordinal))
            {
                return QuantumApiAuthMode.Bearer;
            }

            return QuantumApiAuthMode.ApiKey;
        }

        private static T ParseResponse<T>(string json) where T : class, new()
        {
            if (typeof(T) == typeof(TextTransformResponse))
            {
                return ParseTextTransformResponse(json) as T;
            }

            return QuantumApiJson.TryDeserialize<T>(json);
        }

        private static TextTransformResponse ParseTextTransformResponse(string json)
        {
            var response = QuantumApiJson.TryDeserialize<TextTransformResponse>(json);
            response.category_counts = QuantumApiJson.ParseCategoryCounts(json);
            response.raw_category_counts_json = QuantumApiJson.TryExtractRawFieldValue(json, "category_counts") ?? "{}";
            return response;
        }

        private static bool IsSuccessStatusCode(long statusCode)
        {
            return statusCode >= 200 && statusCode < 300;
        }

        private static string BuildGateRunJson(GateRunRequest request)
        {
            var escapedGateType = EscapeJsonString(request.gate_type ?? string.Empty);
            if (request.sendRotationAngle)
            {
                var rotationAngleJson = request.rotation_angle_rad.ToString(
                    "G9",
                    System.Globalization.CultureInfo.InvariantCulture);
                return $"{{\"gate_type\":\"{escapedGateType}\",\"rotation_angle_rad\":{rotationAngleJson}}}";
            }

            return $"{{\"gate_type\":\"{escapedGateType}\"}}";
        }

        private string BuildRandomJobSubmitJson(RandomJobSubmitRequest request)
        {
            var provider = string.IsNullOrWhiteSpace(request.provider) ? "ibm" : request.provider.Trim();
            var useIbmDefaults = string.Equals(provider, "ibm", StringComparison.OrdinalIgnoreCase);
            var backend = string.IsNullOrWhiteSpace(request.backend_name) && useIbmDefaults
                ? _defaultIbmBackend : (request.backend_name ?? string.Empty).Trim();
            var profile = string.IsNullOrWhiteSpace(request.ibm_profile) && useIbmDefaults
                ? _defaultIbmProfile : (request.ibm_profile ?? string.Empty).Trim();
            var builder = new StringBuilder();
            builder.Append("{");
            builder.Append("\"min\":").Append(request.min.ToString(System.Globalization.CultureInfo.InvariantCulture)).Append(",");
            builder.Append("\"max\":").Append(request.max.ToString(System.Globalization.CultureInfo.InvariantCulture)).Append(",");
            builder.Append("\"provider\":\"").Append(EscapeJsonString(provider)).Append("\",");
            builder.Append("\"backend_name\":\"").Append(EscapeJsonString(backend)).Append("\"");

            if (!string.IsNullOrWhiteSpace(profile))
            {
                builder.Append(",\"ibm_profile\":\"").Append(EscapeJsonString(profile)).Append("\"");
            }

            builder.Append("}");
            return builder.ToString();
        }

        private static string NormalizeProxyUrl(string value)
        {
            var url = (value ?? string.Empty).Trim().TrimEnd('/');
            if (!Uri.TryCreate(url, UriKind.Absolute, out var parsed)
                || (parsed.Scheme != Uri.UriSchemeHttp && parsed.Scheme != Uri.UriSchemeHttps)
                || !string.IsNullOrEmpty(parsed.Query) || !string.IsNullOrEmpty(parsed.Fragment)
                || !string.IsNullOrEmpty(parsed.UserInfo))
            {
                return string.Empty;
            }

            return url.EndsWith("/v1", StringComparison.OrdinalIgnoreCase) ? url : url + "/v1";
        }

        private static string EscapePathSegment(string value)
        {
            return Uri.EscapeDataString(value.Trim());
        }

        private static string EscapeJsonString(string value)
        {
            var sb = new StringBuilder(value.Length);
            foreach (var c in value)
            {
                switch (c)
                {
                    case '"':  sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\b': sb.Append("\\b");  break;
                    case '\f': sb.Append("\\f");  break;
                    case '\n': sb.Append("\\n");  break;
                    case '\r': sb.Append("\\r");  break;
                    case '\t': sb.Append("\\t");  break;
                    default:
                        if (c < 0x20)
                        {
                            sb.Append($"\\u{(int)c:x4}");
                        }
                        else
                        {
                            sb.Append(c);
                        }
                        break;
                }
            }
            return sb.ToString();
        }

        private static Task<T> FailTask<T>(string errorCode, string message) where T : class
        {
            return FailTask<T>(QuantumApiError.Local(errorCode, message));
        }

        private static Task<T> FailTask<T>(QuantumApiError error) where T : class
        {
            var completionSource = new TaskCompletionSource<T>();
            completionSource.SetException(error);
            return completionSource.Task;
        }

        private static int CountWords(string value)
        {
            if (string.IsNullOrWhiteSpace(value))
            {
                return 0;
            }

            return value.Split((char[])null, StringSplitOptions.RemoveEmptyEntries).Length;
        }
    }
}
