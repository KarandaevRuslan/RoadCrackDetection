package com.karandaev.roadCrackDetectionServer.web;

import com.karandaev.roadCrackDetectionServer.image.SafeImage;
import com.karandaev.roadCrackDetectionServer.service.ImageValidationService;
import com.karandaev.roadCrackDetectionServer.yolo.YoloClient;
import com.karandaev.roadCrackDetectionServer.yolo.dto.DetectResponse;
import com.karandaev.roadCrackDetectionServer.yolo.dto.YoloInferResponse;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

@RestController
@RequestMapping("/v1")
public class DetectController {

  private final ImageValidationService imageValidationService;
  private final YoloClient yoloClient;

  public DetectController(ImageValidationService imageValidationService, YoloClient yoloClient) {
    this.imageValidationService = imageValidationService;
    this.yoloClient = yoloClient;
  }

  @PostMapping(value = "/detect", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
  public DetectResponse detect(@RequestPart("file") MultipartFile file) throws IOException {
    byte[] bytes = file.getBytes();

    // 1) проверка валидности/безопасности + нормализация (re-encode)
    SafeImage safe = imageValidationService.validateAndNormalize(bytes);

    // 2) вызов YOLO inference
    YoloInferResponse yolo = yoloClient.infer(safe.normalizedBytes(), safe.format());

    // 3) ответ клиенту
    return new DetectResponse(safe.width(), safe.height(), safe.format(), yolo.detections());
  }
}
