package com.karandaev.roadCrackDetectionServer;

import com.karandaev.roadCrackDetectionServer.image.ImageSecurityProperties;
import com.karandaev.roadCrackDetectionServer.ratelimit.RateLimitProperties;
import com.karandaev.roadCrackDetectionServer.yolo.process.YoloProcessProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

@EnableConfigurationProperties({
  ImageSecurityProperties.class,
  YoloProcessProperties.class,
  RateLimitProperties.class
})
@SpringBootApplication
public class App {
  public static void main(String[] args) {
    SpringApplication.run(App.class, args);
  }
}
