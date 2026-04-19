// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
using System;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;

namespace IO.Swagger.Controllers
{
    /// <summary>
    /// Installs a modifier on the SDK's JsonSerializerOptions so that the
    /// "payload" property of EdgeModuleDirectMethodRequest and DirectMethodResponse
    /// is written/read as raw JSON instead of being base64-encoded.
    /// </summary>
    internal static class PayloadJsonFixup
    {
        internal static void Install(JsonSerializerOptions options)
        {
            // Wrap any existing resolver (the SDK uses DefaultJsonTypeInfoResolver
            // with its own modifiers).
            var existingResolver = options.TypeInfoResolver;
            if (existingResolver == null)
                return;

            options.TypeInfoResolver = existingResolver.WithAddedModifier(FixByteArrayPayload);
        }

        private static void FixByteArrayPayload(JsonTypeInfo typeInfo)
        {
            // Only target EdgeModuleDirectMethodRequest and DirectMethodResponse
            string typeName = typeInfo.Type.Name;
            if (typeName != "EdgeModuleDirectMethodRequest" && typeName != "DirectMethodResponse")
                return;

            foreach (var prop in typeInfo.Properties)
            {
                if (prop.Name == "payload" && prop.PropertyType == typeof(byte[]))
                {
                    // Replace the default byte[] serialization with raw JSON
                    prop.CustomConverter = new RawJsonBytesConverter();
                }
            }
        }
    }

    /// <summary>
    /// JsonConverter for byte[] that writes raw JSON bytes instead of base64.
    /// Only used on specific properties via JsonTypeInfo modifier (not globally).
    /// </summary>
    internal class RawJsonBytesConverter : JsonConverter<byte[]>
    {
        public override byte[] Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            if (reader.TokenType == JsonTokenType.String)
            {
                try
                {
                    return reader.GetBytesFromBase64();
                }
                catch (FormatException)
                {
                    return Encoding.UTF8.GetBytes(reader.GetString());
                }
            }

            if (reader.TokenType == JsonTokenType.Null)
                return null;

            // Capture raw JSON text (object, array, number, bool) as UTF-8 bytes
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

            // Write the bytes as a raw JSON value (not base64).
            writer.WriteRawValue(value);
        }
    }
}
