// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
using System;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace IO.Swagger.Controllers
{
    /// <summary>
    /// Workaround for the v2 preview SDK serialization bug where
    /// EdgeModuleDirectMethodRequest.Payload and DirectMethodResponse.Payload
    /// are declared as <c>byte[]</c> with <c>[JsonProperty("payload")]</c>. With
    /// Newtonsoft's default behavior <c>byte[]</c> is serialized as a base64 string,
    /// so the wire payload becomes <c>{"payload":"&lt;base64&gt;"}</c> instead of
    /// the expected JSON object.
    /// <para>
    /// Scoped to property paths whose final segment is <c>payload</c> so that
    /// other byte[] fields elsewhere in the SDK (e.g. HSM signatures, auth
    /// digests) are NOT touched - applying this converter universally caused
    /// MQTT authentication failures because base64 byte[] auth fields were
    /// being re-interpreted as raw UTF-8 JSON.
    /// </para>
    /// </summary>
    internal class RawJsonByteArrayConverter : JsonConverter
    {
        public override bool CanConvert(Type objectType) => objectType == typeof(byte[]);

        private static bool IsPayloadPath(string path)
        {
            if (string.IsNullOrEmpty(path))
            {
                return false;
            }
            int dot = path.LastIndexOf('.');
            string leaf = dot >= 0 ? path.Substring(dot + 1) : path;
            // strip array indexer [n] if any
            int bracket = leaf.IndexOf('[');
            if (bracket >= 0)
            {
                leaf = leaf.Substring(0, bracket);
            }
            return leaf == "payload" || leaf == "Payload";
        }

        public override object ReadJson(JsonReader reader, Type objectType, object existingValue, JsonSerializer serializer)
        {
            if (reader.TokenType == JsonToken.Null)
            {
                return null;
            }
            if (!IsPayloadPath(reader.Path))
            {
                // Fall back to default base64 byte[] behavior.
                if (reader.TokenType == JsonToken.String)
                {
                    return Convert.FromBase64String((string)reader.Value);
                }
                if (reader.TokenType == JsonToken.StartArray)
                {
                    var arr = JArray.Load(reader);
                    var bytes = new byte[arr.Count];
                    for (int i = 0; i < arr.Count; i++)
                    {
                        bytes[i] = (byte)arr[i];
                    }
                    return bytes;
                }
                return null;
            }

            if (reader.TokenType == JsonToken.String)
            {
                // The wire value is a JSON string. Encode the JSON-escaped
                // string text so callers reading back bytes see the original
                // JSON token text.
                var s = (string)reader.Value;
                return Encoding.UTF8.GetBytes(JsonConvert.ToString(s));
            }
            // Object/array/number/bool: capture the raw JSON text as UTF-8 bytes.
            var token = JToken.ReadFrom(reader);
            return Encoding.UTF8.GetBytes(token.ToString(Formatting.None));
        }

        public override void WriteJson(JsonWriter writer, object value, JsonSerializer serializer)
        {
            var bytes = (byte[])value;
            if (bytes == null)
            {
                writer.WriteNull();
                return;
            }
            if (!IsPayloadPath(writer.Path))
            {
                // Default base64 byte[] representation for non-payload fields.
                writer.WriteValue(bytes);
                return;
            }
            if (bytes.Length == 0)
            {
                // Emit empty array as null to match SDK expectations.
                writer.WriteNull();
                return;
            }
            string text;
            try
            {
                text = Encoding.UTF8.GetString(bytes);
            }
            catch
            {
                writer.WriteValue(bytes);
                return;
            }
            try
            {
                JToken.Parse(text).WriteTo(writer);
            }
            catch (JsonException)
            {
                // Not valid JSON; fall back to default base64 representation.
                writer.WriteValue(bytes);
            }
        }
    }
}

