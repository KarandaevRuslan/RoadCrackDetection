package com.karandaev.roadCrackDetectionServer.image.antivirus;

import com.karandaev.roadCrackDetectionServer.image.ImageSecurityProperties;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableConfigurationProperties(ImageSecurityProperties.class)
public class AntivirusConfig {

  @Bean
  public VirusScanner virusScanner(ImageSecurityProperties props) {
    var av = props.getAntivirus();
    if (!av.isEnabled()) {
      return new NoopVirusScanner();
    }
    return new ClamAvVirusScanner(av.getHost(), av.getPort(), av.getTimeoutMs());
  }

  @Bean
  @ConditionalOnProperty(
      prefix = "image-security.antivirus",
      name = {"enabled", "start-clamd"},
      havingValue = "true")
  public ClamdLifecycle clamdLifecycle(ImageSecurityProperties props) {
    var av = props.getAntivirus();
    return new ClamdLifecycle(
        av.getClamdExe(), av.getClamdConf(), av.getHost(), av.getPort(), av.getStartupTimeoutMs());
  }
}
