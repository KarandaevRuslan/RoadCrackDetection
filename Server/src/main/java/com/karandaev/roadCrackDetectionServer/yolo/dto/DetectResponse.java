package com.karandaev.roadCrackDetectionServer.yolo.dto;

import java.util.List;

public record DetectResponse(
    int imageWidth, int imageHeight, String imageFormat, List<Detection> detections) {}
