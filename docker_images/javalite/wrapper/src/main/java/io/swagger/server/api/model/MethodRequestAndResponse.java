package io.swagger.server.api.model;

import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * parameters and response for a sync method call
 **/
@JsonInclude(JsonInclude.Include.NON_NULL)
public class MethodRequestAndResponse   {

  private Object requestPayload = null;
  private Object responsePayload = null;
  private Integer statusCode = null;

  public MethodRequestAndResponse () {

  }

  public MethodRequestAndResponse (Object requestPayload, Object responsePayload, Integer statusCode) {
    this.requestPayload = requestPayload;
    this.responsePayload = responsePayload;
    this.statusCode = statusCode;
  }


  @JsonProperty("requestPayload")
  public Object getRequestPayload() {
    return requestPayload;
  }
  public void setRequestPayload(Object requestPayload) {
    this.requestPayload = requestPayload;
  }


  @JsonProperty("responsePayload")
  public Object getResponsePayload() {
    return responsePayload;
  }
  public void setResponsePayload(Object responsePayload) {
    this.responsePayload = responsePayload;
  }


  @JsonProperty("statusCode")
  public Integer getStatusCode() {
    return statusCode;
  }
  public void setStatusCode(Integer statusCode) {
    this.statusCode = statusCode;
  }


  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    MethodRequestAndResponse methodRequestAndResponse = (MethodRequestAndResponse) o;
    return Objects.equals(requestPayload, methodRequestAndResponse.requestPayload) &&
        Objects.equals(responsePayload, methodRequestAndResponse.responsePayload) &&
        Objects.equals(statusCode, methodRequestAndResponse.statusCode);
  }

  @Override
  public int hashCode() {
    return Objects.hash(requestPayload, responsePayload, statusCode);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class MethodRequestAndResponse {\n");

    sb.append("    requestPayload: ").append(toIndentedString(requestPayload)).append("\n");
    sb.append("    responsePayload: ").append(toIndentedString(responsePayload)).append("\n");
    sb.append("    statusCode: ").append(toIndentedString(statusCode)).append("\n");
    sb.append("}");
    return sb.toString();
  }

  /**
   * Convert the given object to string with each line indented by 4 spaces
   * (except the first line).
   */
  private String toIndentedString(Object o) {
    if (o == null) {
      return "null";
    }
    return o.toString().replace("\n", "\n    ");
  }
}
