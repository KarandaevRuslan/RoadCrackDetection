package com.karandaev.roadCrackDetectionServer.image;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;

import java.util.List;

@Setter
@Getter
@ConfigurationProperties(prefix = "image-security")
public class ImageSecurityProperties {
  private long maxBytes = 10 * 1024 * 1024;
  private int maxWidth = 4096;
  private int maxHeight = 4096;
  private int maxMegapixels = 20;
  private List<String> allowedFormats = List.of("JPEG", "PNG", "WEBP");
  private String normalizeFormat = "PNG";

  private Antivirus antivirus = new Antivirus();

  @Setter
  @Getter
  public static class Antivirus {
    private boolean enabled = false;

    private String host = "127.0.0.1";
    private int port = 3310;
    private int timeoutMs = 2000;

    // запуск clamd вместе с приложением
    private boolean startClamd = false;

    // пути к clamd (если startClamd=true)
    private String clamdExe; // например: C:/.../clamd.exe
    private String clamdConf; // например: C:/.../clamd.conf

    private int startupTimeoutMs = 15000;
  }
}
