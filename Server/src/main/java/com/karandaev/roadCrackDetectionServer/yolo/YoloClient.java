package com.karandaev.roadCrackDetectionServer.yolo;

import com.karandaev.roadCrackDetectionServer.yolo.dto.YoloInferResponse;

public interface YoloClient {
  YoloInferResponse infer(byte[] imageBytes, String imageFormat);
}
