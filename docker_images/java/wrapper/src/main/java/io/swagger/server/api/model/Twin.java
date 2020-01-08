package io.swagger.server.api.model;

import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * device twin or module twin
 **/
@JsonInclude(JsonInclude.Include.NON_NULL)
public class Twin   {

  private Object desired = null;
  private Object reported = null;

  public Twin () {

  }

  public Twin (Object desired, Object reported) {
    this.desired = desired;
    this.reported = reported;
  }


  @JsonProperty("desired")
  public Object getDesired() {
    return desired;
  }
  public void setDesired(Object desired) {
    this.desired = desired;
  }


  @JsonProperty("reported")
  public Object getReported() {
    return reported;
  }
  public void setReported(Object reported) {
    this.reported = reported;
  }


  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    Twin twin = (Twin) o;
    return Objects.equals(desired, twin.desired) &&
        Objects.equals(reported, twin.reported);
  }

  @Override
  public int hashCode() {
    return Objects.hash(desired, reported);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class Twin {\n");

    sb.append("    desired: ").append(toIndentedString(desired)).append("\n");
    sb.append("    reported: ").append(toIndentedString(reported)).append("\n");
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
