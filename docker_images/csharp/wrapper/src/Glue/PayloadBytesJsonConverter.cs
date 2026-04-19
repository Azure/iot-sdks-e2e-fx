// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
using System;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace IO.Swagger.Controllers
{
    /// <summary>
    /// Custom JsonConverter for byte[] that writes raw JSON bytes instead of
    /// base64-encoding them.  The Azure IoT C# SDK v2 serializes
    /// EdgeModuleDirectMethodRequest via System.Text.Json which base64-encodes
    /// byte[] properties by default.  EdgeHub expects the 'payload' field to
    /// be a raw JSON value, not a base64 string.
    /// </summary>
    internal class PayloadBytesJsonConverter : JsonConverter<byte[]>
    {
        public override byte[] Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            if (reader.TokenType == JsonTokenType.String)
            {
                // Try base64 first (backward compat with responses that may use it)
                try
                {
                    return reader.GetBytesFromBase64();
                }
                catch (FormatException)
                {
                    // Not valid base64 — treat as a raw JSON string value
                    return Encoding.UTF8.GetBytes(reader.GetString());
                }
            }

            if (reader.TokenType == JsonTokenType.Null)
            {
                return null;
            }

            // For any other JSON token (object, array, number, bool), capture
            // the raw JSON text and return it as UTF-8 bytes.
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

            // Write the bytes directly as a raw JSON value.  The bytes are
            // expected to contain valid UTF-8 JSON (e.g. '{"key":"value"}').
            writer.WriteRawValue(value);
        }
    }
}
