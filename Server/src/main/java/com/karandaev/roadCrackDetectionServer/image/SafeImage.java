package com.karandaev.roadCrackDetectionServer.image;

public record SafeImage(
    byte[] normalizedBytes, // байты пересохраненного изображения
    int width, // ширина (пиксели)
    int height, // высота (пиксели)
    String format // формат нормализации (PNG/JPEG)
    ) {}
