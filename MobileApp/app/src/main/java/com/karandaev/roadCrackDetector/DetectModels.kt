package com.karandaev.roadCrackDetector

data class BBox(
    val xMin: Int,
    val yMin: Int,
    val xMax: Int,
    val yMax: Int
)

data class Detection(
    val clazz: String,
    val confidence: Double,
    val bbox: BBox
)

data class DetectResponse(
    val imageWidth: Int,
    val imageHeight: Int,
    val imageFormat: String,
    val detections: List<Detection>
)