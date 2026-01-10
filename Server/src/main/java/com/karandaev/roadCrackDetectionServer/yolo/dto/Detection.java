package com.karandaev.roadCrackDetectionServer.yolo.dto;

public record Detection(
    String clazz, // "class" слово зарезервировано в Java, поэтому clazz
    double confidence, // уверенность 0..1
    BBox bbox) {}
