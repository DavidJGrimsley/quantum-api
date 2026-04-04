using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Globalization;

namespace QuantumApi.Unity
{
    public sealed class QuantumApiError : Exception
    {
        public long StatusCode { get; }
        public string ErrorCode { get; }
        public string RequestId { get; }
        public string DetailsJson { get; }
        public string ResponseBody { get; }
        public IReadOnlyDictionary<string, string> Headers { get; }
        public int? RateLimitLimit { get; }
        public int? RateLimitRemaining { get; }
        public int? RateLimitReset { get; }
        public int? RetryAfter { get; }

        internal QuantumApiError(
            string message,
            long statusCode,
            string errorCode,
            string requestId,
            string detailsJson,
            string responseBody,
            IDictionary<string, string> headers)
            : base(message)
        {
            StatusCode = statusCode;
            ErrorCode = errorCode ?? "";
            RequestId = requestId ?? "";
            DetailsJson = detailsJson ?? "";
            ResponseBody = responseBody ?? "";

            var copiedHeaders = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            if (headers != null)
            {
                foreach (var pair in headers)
                {
                    copiedHeaders[pair.Key] = pair.Value;
                }
            }

            Headers = new ReadOnlyDictionary<string, string>(copiedHeaders);
            RateLimitLimit = ParseOptionalInt(copiedHeaders, "RateLimit-Limit");
            RateLimitRemaining = ParseOptionalInt(copiedHeaders, "RateLimit-Remaining");
            RateLimitReset = ParseOptionalInt(copiedHeaders, "RateLimit-Reset");
            RetryAfter = ParseOptionalInt(copiedHeaders, "Retry-After");
        }

        internal static QuantumApiError Local(string errorCode, string message)
        {
            return new QuantumApiError(
                message,
                0,
                errorCode,
                "",
                "",
                "",
                new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase));
        }

        internal static QuantumApiError FromResponse(
            long statusCode,
            string responseBody,
            IDictionary<string, string> headers)
        {
            var envelope = QuantumApiJson.TryDeserialize<QuantumApiErrorEnvelope>(responseBody);
            var message = string.IsNullOrWhiteSpace(envelope.message)
                ? $"Quantum API request failed with status {statusCode}"
                : envelope.message;

            return new QuantumApiError(
                message,
                statusCode,
                envelope.error,
                envelope.request_id,
                QuantumApiJson.TryExtractRawFieldValue(responseBody, "details"),
                responseBody,
                headers);
        }

        private static int? ParseOptionalInt(IDictionary<string, string> headers, string headerName)
        {
            if (headers == null || !headers.TryGetValue(headerName, out var rawValue))
            {
                return null;
            }

            return int.TryParse(rawValue, NumberStyles.Integer, CultureInfo.InvariantCulture, out var parsed)
                ? parsed
                : null;
        }
    }
}
