package com.karandaev.roadCrackDetectionServer.yolo.http;

import com.karandaev.roadCrackDetectionServer.yolo.YoloClient;
import com.karandaev.roadCrackDetectionServer.yolo.YoloClientException;
import com.karandaev.roadCrackDetectionServer.yolo.dto.YoloInferResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.Duration;

@Component
public class YoloHttpClient implements YoloClient {

  private final WebClient webClient;
  private final String detectPath;
  private final Duration timeout;

  public YoloHttpClient(
      WebClient yoloWebClient,
      @Value("${yolo.detect-path}") String detectPath,
      @Value("${yolo.timeout-ms}") long timeoutMs) {
    this.webClient = yoloWebClient;
    this.detectPath = detectPath;
    this.timeout = Duration.ofMillis(timeoutMs);
  }

  @Override
  public YoloInferResponse infer(byte[] imageBytes, String imageFormat) {
    // imageFormat: "PNG" или "JPEG" — используем для Content-Type
    MediaType contentType =
        switch (imageFormat.toUpperCase()) {
          case "JPEG", "JPG" -> MediaType.IMAGE_JPEG;
          case "PNG" -> MediaType.IMAGE_PNG;
          case "WEBP" -> MediaType.valueOf("image/webp");
          default -> MediaType.APPLICATION_OCTET_STREAM;
        };

    try {
      return webClient
          .post()
          .uri(detectPath)
          .contentType(contentType)
          .accept(MediaType.APPLICATION_JSON)
          .bodyValue(imageBytes)
          .retrieve()
          .bodyToMono(YoloInferResponse.class)
          .timeout(timeout)
          .block();
    } catch (Exception e) {
      throw new YoloClientException("YOLO inference call failed", e);
    }
  }
}
