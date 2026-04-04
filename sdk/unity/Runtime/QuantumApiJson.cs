using System;
using System.Collections.Generic;
using System.Globalization;
using UnityEngine;

namespace QuantumApi.Unity
{
    internal static class QuantumApiJson
    {
        public static string Serialize(object value)
        {
            return JsonUtility.ToJson(value);
        }

        public static T TryDeserialize<T>(string json) where T : class, new()
        {
            if (string.IsNullOrWhiteSpace(json))
            {
                return new T();
            }

            try
            {
                return JsonUtility.FromJson<T>(json) ?? new T();
            }
            catch
            {
                return new T();
            }
        }

        public static string TryExtractRawFieldValue(string json, string fieldName)
        {
            if (string.IsNullOrWhiteSpace(json) || string.IsNullOrWhiteSpace(fieldName))
            {
                return null;
            }

            if (!TryFindValueRange(json, fieldName, out var start, out var end))
            {
                return null;
            }

            return json.Substring(start, end - start);
        }

        public static List<CategoryCountEntry> ParseCategoryCounts(string json)
        {
            return ParseFlatIntegerObject(TryExtractRawFieldValue(json, "category_counts"));
        }

        private static List<CategoryCountEntry> ParseFlatIntegerObject(string objectJson)
        {
            var entries = new List<CategoryCountEntry>();
            if (string.IsNullOrWhiteSpace(objectJson))
            {
                return entries;
            }

            var index = 0;
            SkipWhitespace(objectJson, ref index);
            if (index >= objectJson.Length || objectJson[index] != '{')
            {
                return entries;
            }

            index += 1;
            while (index < objectJson.Length)
            {
                SkipWhitespace(objectJson, ref index);
                if (index >= objectJson.Length || objectJson[index] == '}')
                {
                    break;
                }

                if (objectJson[index] == ',')
                {
                    index += 1;
                    continue;
                }

                if (objectJson[index] != '"')
                {
                    break;
                }

                var keyEnd = FindStringEnd(objectJson, index + 1);
                if (keyEnd < 0)
                {
                    break;
                }

                var key = UnescapeJsonString(objectJson.Substring(index + 1, keyEnd - index - 1));
                index = keyEnd + 1;
                SkipWhitespace(objectJson, ref index);
                if (index >= objectJson.Length || objectJson[index] != ':')
                {
                    break;
                }

                index += 1;
                SkipWhitespace(objectJson, ref index);

                var valueStart = index;
                while (index < objectJson.Length && objectJson[index] != ',' && objectJson[index] != '}')
                {
                    index += 1;
                }

                var numericToken = objectJson.Substring(valueStart, index - valueStart).Trim();
                if (int.TryParse(numericToken, NumberStyles.Integer, CultureInfo.InvariantCulture, out var integerCount))
                {
                    entries.Add(new CategoryCountEntry { category = key, count = integerCount });
                }
                else if (double.TryParse(numericToken, NumberStyles.Float, CultureInfo.InvariantCulture, out var floatCount))
                {
                    entries.Add(new CategoryCountEntry { category = key, count = (int)Math.Round(floatCount) });
                }
            }

            return entries;
        }

        private static bool TryFindValueRange(string json, string fieldName, out int start, out int end)
        {
            var fieldToken = "\"" + fieldName + "\"";
            var searchIndex = 0;

            while (true)
            {
                var fieldIndex = json.IndexOf(fieldToken, searchIndex, StringComparison.Ordinal);
                if (fieldIndex < 0)
                {
                    start = 0;
                    end = 0;
                    return false;
                }

                var cursor = fieldIndex + fieldToken.Length;
                SkipWhitespace(json, ref cursor);
                if (cursor >= json.Length || json[cursor] != ':')
                {
                    searchIndex = fieldIndex + fieldToken.Length;
                    continue;
                }

                cursor += 1;
                SkipWhitespace(json, ref cursor);
                if (cursor >= json.Length)
                {
                    start = 0;
                    end = 0;
                    return false;
                }

                start = cursor;
                var first = json[cursor];
                if (first == '"')
                {
                    var stringEnd = FindStringEnd(json, cursor + 1);
                    if (stringEnd < 0)
                    {
                        end = start;
                        return false;
                    }

                    end = stringEnd + 1;
                    return true;
                }

                if (first == '{' || first == '[')
                {
                    var matching = first == '{' ? '}' : ']';
                    var containerEnd = FindContainerEnd(json, cursor, first, matching);
                    if (containerEnd < 0)
                    {
                        end = start;
                        return false;
                    }

                    end = containerEnd + 1;
                    return true;
                }

                var valueEnd = cursor;
                while (valueEnd < json.Length && json[valueEnd] != ',' && json[valueEnd] != '}' && json[valueEnd] != ']')
                {
                    valueEnd += 1;
                }

                end = valueEnd;
                while (end > start && char.IsWhiteSpace(json[end - 1]))
                {
                    end -= 1;
                }

                return end > start;
            }
        }

        private static int FindStringEnd(string json, int startIndex)
        {
            var escaped = false;
            for (var index = startIndex; index < json.Length; index += 1)
            {
                var current = json[index];
                if (escaped)
                {
                    escaped = false;
                    continue;
                }

                if (current == '\\')
                {
                    escaped = true;
                    continue;
                }

                if (current == '"')
                {
                    return index;
                }
            }

            return -1;
        }

        private static int FindContainerEnd(string json, int startIndex, char open, char close)
        {
            var depth = 0;
            var inString = false;
            var escaped = false;

            for (var index = startIndex; index < json.Length; index += 1)
            {
                var current = json[index];
                if (inString)
                {
                    if (escaped)
                    {
                        escaped = false;
                    }
                    else if (current == '\\')
                    {
                        escaped = true;
                    }
                    else if (current == '"')
                    {
                        inString = false;
                    }

                    continue;
                }

                if (current == '"')
                {
                    inString = true;
                    continue;
                }

                if (current == open)
                {
                    depth += 1;
                    continue;
                }

                if (current == close)
                {
                    depth -= 1;
                    if (depth == 0)
                    {
                        return index;
                    }
                }
            }

            return -1;
        }

        private static void SkipWhitespace(string value, ref int index)
        {
            while (index < value.Length && char.IsWhiteSpace(value[index]))
            {
                index += 1;
            }
        }

        private static string UnescapeJsonString(string value)
        {
            return value
                .Replace("\\\"", "\"")
                .Replace("\\\\", "\\")
                .Replace("\\/", "/")
                .Replace("\\b", "\b")
                .Replace("\\f", "\f")
                .Replace("\\n", "\n")
                .Replace("\\r", "\r")
                .Replace("\\t", "\t");
        }
    }
}
