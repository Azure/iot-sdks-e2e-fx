package io.swagger.server.api.model;

import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * body for an invoming or outgoing event or message
 **/
@JsonInclude(JsonInclude.Include.NON_NULL)
public class EventBody   {

  private Object body = null;
  private Object hortonFlags = null;
  private Object attributes = null;

  public EventBody () {

  }

  public EventBody (Object body, Object hortonFlags, Object attributes) {
    this.body = body;
    this.hortonFlags = hortonFlags;
    this.attributes = attributes;
  }


  @JsonProperty("body")
  public Object getBody() {
    return body;
  }
  public void setBody(Object body) {
    this.body = body;
  }


  @JsonProperty("horton_flags")
  public Object getHortonFlags() {
    return hortonFlags;
  }
  public void setHortonFlags(Object hortonFlags) {
    this.hortonFlags = hortonFlags;
  }


  @JsonProperty("attributes")
  public Object getAttributes() {
    return attributes;
  }
  public void setAttributes(Object attributes) {
    this.attributes = attributes;
  }


  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    EventBody eventBody = (EventBody) o;
    return Objects.equals(body, eventBody.body) &&
        Objects.equals(hortonFlags, eventBody.hortonFlags) &&
        Objects.equals(attributes, eventBody.attributes);
  }

  @Override
  public int hashCode() {
    return Objects.hash(body, hortonFlags, attributes);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class EventBody {\n");

    sb.append("    body: ").append(toIndentedString(body)).append("\n");
    sb.append("    hortonFlags: ").append(toIndentedString(hortonFlags)).append("\n");
    sb.append("    attributes: ").append(toIndentedString(attributes)).append("\n");
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
