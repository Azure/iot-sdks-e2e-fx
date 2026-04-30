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
    /// EdgeModuleDirectMethodRequest.Payload and DirectMethodClientResponse.Payload
    /// are declared as <c>byte[]</c> with <c>[JsonProperty("payload")]</c>. With
    /// Newtonsoft's default behavior <c>byte[]</c> is serialized as a base64 string,
    /// so the wire payload becomes <c>{"payload":"&lt;base64&gt;"}</c> instead of
    /// the expected JSON object. This converter, when registered globally via
    /// <see cref="JsonConvert.DefaultSettings"/>, treats <c>byte[]</c> contents as
    /// raw UTF-8 JSON when valid (and falls back to base64 otherwise).
    /// </summary>
    internal class RawJsonByteArrayConverter : JsonConverter
    {
        public override bool CanConvert(Type objectType) => objectType == typeof(byte[]);

        public override object ReadJson(JsonReader reader, Type objectType, object existingValue, JsonSerializer serializer)
        {
            if (reader.TokenType == JsonToken.Null)
            {
                return null;
            }
            if (reader.TokenType == JsonToken.String)
            {
                // The wire value is a JSON string. Preserve the bytes as the UTF-8
                // encoding of the JSON-encoded string (so callers reading the bytes
                // see the original JSON value text).
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
            Console.WriteLine($"RawJsonByteArrayConverter.WriteJson invoked: bytes.Length={bytes?.Length}");
            if (bytes == null)
            {
                writer.WriteNull();
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
