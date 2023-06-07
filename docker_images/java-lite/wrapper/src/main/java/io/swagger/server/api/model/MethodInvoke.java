package io.swagger.server.api.model;

import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * parameters used to invoke a method
 **/
@JsonInclude(JsonInclude.Include.NON_NULL)
public class MethodInvoke   {

  private String methodName = null;
  private Object payload = null;
  private Integer responseTimeoutInSeconds = null;
  private Integer connectTimeoutInSeconds = null;

  public MethodInvoke () {

  }

  public MethodInvoke (String methodName, Object payload, Integer responseTimeoutInSeconds, Integer connectTimeoutInSeconds) {
    this.methodName = methodName;
    this.payload = payload;
    this.responseTimeoutInSeconds = responseTimeoutInSeconds;
    this.connectTimeoutInSeconds = connectTimeoutInSeconds;
  }


  @JsonProperty("methodName")
  public String getMethodName() {
    return methodName;
  }
  public void setMethodName(String methodName) {
    this.methodName = methodName;
  }


  @JsonProperty("payload")
  public Object getPayload() {
    return payload;
  }
  public void setPayload(Object payload) {
    this.payload = payload;
  }


  @JsonProperty("responseTimeoutInSeconds")
  public Integer getResponseTimeoutInSeconds() {
    return responseTimeoutInSeconds;
  }
  public void setResponseTimeoutInSeconds(Integer responseTimeoutInSeconds) {
    this.responseTimeoutInSeconds = responseTimeoutInSeconds;
  }


  @JsonProperty("connectTimeoutInSeconds")
  public Integer getConnectTimeoutInSeconds() {
    return connectTimeoutInSeconds;
  }
  public void setConnectTimeoutInSeconds(Integer connectTimeoutInSeconds) {
    this.connectTimeoutInSeconds = connectTimeoutInSeconds;
  }


  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    MethodInvoke methodInvoke = (MethodInvoke) o;
    return Objects.equals(methodName, methodInvoke.methodName) &&
        Objects.equals(payload, methodInvoke.payload) &&
        Objects.equals(responseTimeoutInSeconds, methodInvoke.responseTimeoutInSeconds) &&
        Objects.equals(connectTimeoutInSeconds, methodInvoke.connectTimeoutInSeconds);
  }

  @Override
  public int hashCode() {
    return Objects.hash(methodName, payload, responseTimeoutInSeconds, connectTimeoutInSeconds);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class MethodInvoke {\n");

    sb.append("    methodName: ").append(toIndentedString(methodName)).append("\n");
    sb.append("    payload: ").append(toIndentedString(payload)).append("\n");
    sb.append("    responseTimeoutInSeconds: ").append(toIndentedString(responseTimeoutInSeconds)).append("\n");
    sb.append("    connectTimeoutInSeconds: ").append(toIndentedString(connectTimeoutInSeconds)).append("\n");
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
