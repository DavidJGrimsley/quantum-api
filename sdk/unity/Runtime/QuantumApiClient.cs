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
        private readonly string _baseUrl;
        private readonly bool _backendProxyMode;
        private readonly string _apiKey;
        private readonly string _bearerToken;
        private readonly QuantumApiAuthMode _defaultAuthMode;
        private readonly int _timeoutSeconds;

        public QuantumApiClient(QuantumApiClientOptions options)
        {
            if (options == null)
            {
                throw new ArgumentNullException(nameof(options));
            }

            _baseUrl = NormalizeBaseUrl(options.BaseUrl);
            _backendProxyMode = options.BackendProxyMode;
            _apiKey = (options.ApiKey ?? string.Empty).Trim();
            _bearerToken = (options.BearerToken ?? string.Empty).Trim();
            _defaultAuthMode = options.DefaultAuthMode;
            _timeoutSeconds = options.TimeoutSeconds > 0 ? options.TimeoutSeconds : 15;
        }

        public string BaseUrl => _baseUrl;

        public bool BackendProxyMode => _backendProxyMode;

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

            return SendAsync<GateRunResponse>("/gates/run", UnityWebRequest.kHttpVerbPOST, request, requestOptions);
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

            yield return SendCoroutine("/gates/run", UnityWebRequest.kHttpVerbPOST, request, onSuccess, onError, requestOptions);
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

            if (resolvedAuthMode == QuantumApiAuthMode.ApiKey && string.IsNullOrWhiteSpace(apiKey))
            {
                configurationError = QuantumApiError.Local(
                    "missing_api_key",
                    $"Quantum API request to {path} requires an API key.");
                return null;
            }

            if (resolvedAuthMode == QuantumApiAuthMode.Bearer && string.IsNullOrWhiteSpace(bearerToken))
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
                    request.SetRequestHeader(pair.Key, pair.Value);
                }
            }

            request.SetRequestHeader("Accept", "application/json");

            if (body != null)
            {
                var payloadJson = QuantumApiJson.Serialize(body);
                request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(payloadJson));
                request.SetRequestHeader("Content-Type", "application/json");
            }

            if (resolvedAuthMode == QuantumApiAuthMode.ApiKey)
            {
                request.SetRequestHeader("X-API-Key", apiKey);
            }
            else if (resolvedAuthMode == QuantumApiAuthMode.Bearer)
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

            if (_backendProxyMode)
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

        private static string NormalizeBaseUrl(string baseUrl)
        {
            var trimmed = (baseUrl ?? string.Empty).Trim().TrimEnd('/');
            if (string.IsNullOrWhiteSpace(trimmed))
            {
                throw new ArgumentException("QuantumApiClient requires a non-empty BaseUrl.", nameof(baseUrl));
            }

            return trimmed.EndsWith("/v1", StringComparison.Ordinal) ? trimmed : trimmed + "/v1";
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
