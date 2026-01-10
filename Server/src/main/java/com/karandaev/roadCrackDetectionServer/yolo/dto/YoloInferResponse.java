package com.karandaev.roadCrackDetectionServer.yolo.dto;

import java.util.List;

public record YoloInferResponse(List<Detection> detections) {}
