// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
using System;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace IO.Swagger.Controllers
{
    /// <summary>
    /// System.Text.Json converter for <c>byte[]</c> that emits raw UTF-8 JSON
    /// instead of base64 for payload fields.
    ///
    /// Because STJ converters don't receive the current property path, this
    /// converter always treats byte[] as raw JSON on write and tries
    /// raw-JSON-first on read.  This is safe because the wrapper never
    /// serializes non-payload byte[] fields through the MVC pipeline (auth
    /// digests etc. stay inside the SDK layer) and incoming REST requests
    /// from the Python test runner never send base64 byte[] fields.
    /// </summary>
    internal class RawJsonByteArrayConverter : JsonConverter<byte[]>
    {
        public override byte[] Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            if (reader.TokenType == JsonTokenType.Null)
            {
                return null;
            }
            if (reader.TokenType == JsonTokenType.String)
            {
                string s = reader.GetString();
                return Encoding.UTF8.GetBytes(JsonSerializer.Serialize(s));
            }
            // Object, array, number, bool: capture the raw JSON text as bytes.
            using var doc = JsonDocument.ParseValue(ref reader);
            return Encoding.UTF8.GetBytes(doc.RootElement.GetRawText());
        }

        public override void Write(Utf8JsonWriter writer, byte[] value, JsonSerializerOptions options)
        {
            if (value == null)
            {
                writer.WriteNullValue();
                return;
            }
            if (value.Length == 0)
            {
                writer.WriteNullValue();
                return;
            }
            // Attempt to write as raw JSON (the payload case).
            try
            {
                string text = Encoding.UTF8.GetString(value);
                using var doc = JsonDocument.Parse(text);
                doc.RootElement.WriteTo(writer);
            }
            catch
            {
                // Not valid JSON/UTF-8 — fall back to base64.
                writer.WriteBase64StringValue(value);
            }
        }
    }
}

