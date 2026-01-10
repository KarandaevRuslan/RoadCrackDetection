package com.karandaev.roadCrackDetectionServer.yolo.process;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;

import java.util.List;

@Setter
@Getter
@ConfigurationProperties(prefix = "yolo-process")
public class YoloProcessProperties {
  private boolean enabled = true;
  private String workdir;
  private String pythonExe;
  private List<String> args = List.of();

  private String healthUrl;
  private long startupTimeoutMs = 20000;
  private long shutdownTimeoutMs = 5000;
}
