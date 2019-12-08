/*
 * Azure IOT End-to-End Test Wrapper Rest Api
 *
 * REST API definition for End-to-end testing of the Azure IoT SDKs.  All SDK APIs that are tested by our E2E tests need to be defined in this file.  This file takes some liberties with the API definitions.  In particular, response schemas are undefined, and error responses are also undefined.
 *
 * OpenAPI spec version: 1.0.0
 * 
 * Generated by: https://github.com/swagger-api/swagger-codegen.git
 */

using System;
using System.Linq;
using System.IO;
using System.Text;
using System.Collections;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel.DataAnnotations;
using System.Runtime.Serialization;
using Newtonsoft.Json;

namespace IO.Swagger.Models
{ 
    /// <summary>
    /// parameters and response for a sync method call
    /// </summary>
    [DataContract]
    public partial class RoundtripMethodCallBody : IEquatable<RoundtripMethodCallBody>
    { 
        /// <summary>
        /// payload for the request that arrived from the service.  Used to verify that the correct request arrived.
        /// </summary>
        /// <value>payload for the request that arrived from the service.  Used to verify that the correct request arrived.</value>
        [DataMember(Name="requestPayload")]
        public Object RequestPayload { get; set; }

        /// <summary>
        /// payload for the response to return to the service.  Used to verify that the correct request arrived.
        /// </summary>
        /// <value>payload for the response to return to the service.  Used to verify that the correct request arrived.</value>
        [DataMember(Name="responsePayload")]
        public Object ResponsePayload { get; set; }

        /// <summary>
        /// status code to return to the service
        /// </summary>
        /// <value>status code to return to the service</value>
        [DataMember(Name="statusCode")]
        public int? StatusCode { get; set; }

        /// <summary>
        /// Returns the string presentation of the object
        /// </summary>
        /// <returns>String presentation of the object</returns>
        public override string ToString()
        {
            var sb = new StringBuilder();
            sb.Append("class RoundtripMethodCallBody {\n");
            sb.Append("  RequestPayload: ").Append(RequestPayload).Append("\n");
            sb.Append("  ResponsePayload: ").Append(ResponsePayload).Append("\n");
            sb.Append("  StatusCode: ").Append(StatusCode).Append("\n");
            sb.Append("}\n");
            return sb.ToString();
        }

        /// <summary>
        /// Returns the JSON string presentation of the object
        /// </summary>
        /// <returns>JSON string presentation of the object</returns>
        public string ToJson()
        {
            return JsonConvert.SerializeObject(this, Formatting.Indented);
        }

        /// <summary>
        /// Returns true if objects are equal
        /// </summary>
        /// <param name="obj">Object to be compared</param>
        /// <returns>Boolean</returns>
        public override bool Equals(object obj)
        {
            if (ReferenceEquals(null, obj)) return false;
            if (ReferenceEquals(this, obj)) return true;
            return obj.GetType() == GetType() && Equals((RoundtripMethodCallBody)obj);
        }

        /// <summary>
        /// Returns true if RoundtripMethodCallBody instances are equal
        /// </summary>
        /// <param name="other">Instance of RoundtripMethodCallBody to be compared</param>
        /// <returns>Boolean</returns>
        public bool Equals(RoundtripMethodCallBody other)
        {
            if (ReferenceEquals(null, other)) return false;
            if (ReferenceEquals(this, other)) return true;

            return 
                (
                    RequestPayload == other.RequestPayload ||
                    RequestPayload != null &&
                    RequestPayload.Equals(other.RequestPayload)
                ) && 
                (
                    ResponsePayload == other.ResponsePayload ||
                    ResponsePayload != null &&
                    ResponsePayload.Equals(other.ResponsePayload)
                ) && 
                (
                    StatusCode == other.StatusCode ||
                    StatusCode != null &&
                    StatusCode.Equals(other.StatusCode)
                );
        }

        /// <summary>
        /// Gets the hash code
        /// </summary>
        /// <returns>Hash code</returns>
        public override int GetHashCode()
        {
            unchecked // Overflow is fine, just wrap
            {
                var hashCode = 41;
                // Suitable nullity checks etc, of course :)
                    if (RequestPayload != null)
                    hashCode = hashCode * 59 + RequestPayload.GetHashCode();
                    if (ResponsePayload != null)
                    hashCode = hashCode * 59 + ResponsePayload.GetHashCode();
                    if (StatusCode != null)
                    hashCode = hashCode * 59 + StatusCode.GetHashCode();
                return hashCode;
            }
        }

        #region Operators
        #pragma warning disable 1591

        public static bool operator ==(RoundtripMethodCallBody left, RoundtripMethodCallBody right)
        {
            return Equals(left, right);
        }

        public static bool operator !=(RoundtripMethodCallBody left, RoundtripMethodCallBody right)
        {
            return !Equals(left, right);
        }

        #pragma warning restore 1591
        #endregion Operators
    }
}
