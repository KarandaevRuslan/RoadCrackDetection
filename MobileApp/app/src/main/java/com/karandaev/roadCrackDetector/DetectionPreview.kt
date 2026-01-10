package com.karandaev.roadCrackDetector

import android.graphics.Paint
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.drawIntoCanvas
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import kotlin.math.min

@Composable
fun DetectionPreview(
    imageUri: android.net.Uri,
    response: DetectResponse?
) {
    Card {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Image preview", style = MaterialTheme.typography.titleMedium)

            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(320.dp),
                contentAlignment = Alignment.Center
            ) {
                var boxSize by remember { mutableStateOf(IntSize(1, 1)) }

                // We use the same size for Image and overlay Canvas.
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .onSizeChanged { boxSize = it }
                ) {
                    AsyncImage(
                        model = imageUri,
                        contentDescription = "Selected image",
                        modifier = Modifier.fillMaxSize(),
                        contentScale = ContentScale.Fit
                    )

                    if (response != null) {
                        DetectionOverlay(
                            containerSize = boxSize,
                            imageWidth = response.imageWidth,
                            imageHeight = response.imageHeight,
                            detections = response.detections
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun DetectionOverlay(
    containerSize: IntSize,
    imageWidth: Int,
    imageHeight: Int,
    detections: List<Detection>
) {
    val density = LocalDensity.current
    val strokePx = with(density) { 2.dp.toPx() }
    val textPx = with(density) { 12.dp.toPx() }

    // Compute "fit" transform: scale + offsets to center the image inside the container.
    val cw = containerSize.width.toFloat()
    val ch = containerSize.height.toFloat()

    val sx = cw / imageWidth.toFloat()
    val sy = ch / imageHeight.toFloat()
    val scale = min(sx, sy)

    val drawnW = imageWidth * scale
    val drawnH = imageHeight * scale
    val offsetX = (cw - drawnW) / 2f
    val offsetY = (ch - drawnH) / 2f

    androidx.compose.foundation.Canvas(modifier = Modifier.fillMaxSize()) {
        // Android Paint for text (Compose canvas text is limited)
        val paint = Paint().apply {
            isAntiAlias = true
            textSize = textPx
            style = Paint.Style.FILL
        }

        detections.forEach { det ->
            val color = classColor(det.clazz)

            val left = offsetX + det.bbox.xMin * scale
            val top = offsetY + det.bbox.yMin * scale
            val right = offsetX + det.bbox.xMax * scale
            val bottom = offsetY + det.bbox.yMax * scale

            // Rectangle stroke (no fill)
            drawRect(
                color = color,
                topLeft = Offset(left, top),
                size = androidx.compose.ui.geometry.Size(right - left, bottom - top),
                style = Stroke(width = strokePx)
            )

            // Label near the top-left corner
            val label = "${det.clazz} ${"%.2f".format(det.confidence)}"
            drawIntoCanvas { canvas ->
                paint.color = color.toArgb()
                // place text slightly above the box, but not outside too much
                val textX = left
                val textY = (top - 6f).coerceAtLeast(textPx)
                canvas.nativeCanvas.drawText(label, textX, textY, paint)
            }
        }
    }
}

private fun classColor(clazz: String): Color {
    // Deterministic color from class string hash (stable per class)
    val h = (clazz.hashCode() and 0xFFFF) % 360
    val hsv = floatArrayOf(h.toFloat(), 0.85f, 0.90f)
    val argb = android.graphics.Color.HSVToColor(hsv)
    return Color(argb)
}
