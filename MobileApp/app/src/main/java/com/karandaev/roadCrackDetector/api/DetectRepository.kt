package com.karandaev.roadCrackDetector.api

import android.content.Context
import android.net.Uri
import com.google.firebase.auth.FirebaseAuth
import com.karandaev.roadCrackDetector.BBox
import com.karandaev.roadCrackDetector.DetectResponse
import kotlinx.coroutines.tasks.await
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import com.karandaev.roadCrackDetector.Detection
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class DetectRepository(
    private val auth: FirebaseAuth,
    private val baseUrl: String,
    private val http: OkHttpClient = OkHttpClient()
) {

    suspend fun detect(context: Context, imageUri: Uri): Pair<DetectResponse, String> =
        withContext(Dispatchers.IO) {
            val bytes = context.contentResolver.openInputStream(imageUri)?.use { it.readBytes() }
                ?: error("Could not read the selected image.")

            // Client-side limit check (matches backend: 10MB)
            if (bytes.size > 10 * 1024 * 1024) {
                throw IllegalArgumentException("Image is too large. Max size is 10 MB.")
            }

            val tempFile = File(context.cacheDir, "detect_upload_${System.currentTimeMillis()}.bin")
            FileOutputStream(tempFile).use { it.write(bytes) }

            val mime = context.contentResolver.getType(imageUri) ?: "application/octet-stream"
            val mediaType = mime.toMediaTypeOrNull()

            val filePart = tempFile.asRequestBody(mediaType)
            val multipart = MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart(
                    name = "file",
                    filename = "image.${guessExtension(mime)}",
                    body = filePart
                )
                .build()

            val token = auth.currentUser?.getIdToken(false)?.await()?.token
            val request = Request.Builder()
                .url("${baseUrl.trimEnd('/')}/v1/detect")
                .post(multipart)
                .apply {
                    if (!token.isNullOrBlank()) header("Authorization", "Bearer $token")
                }
                .build()

            http.newCall(request).execute().use { resp ->
                val body = resp.body?.string().orEmpty()

                if (!resp.isSuccessful) {
                    throw HttpFailure(resp.code, body)
                }

                val parsed = parseDetectResponse(body)
                parsed to prettyJson(body)
            }
        }

    private fun guessExtension(mime: String): String = when (mime.lowercase()) {
        "image/jpeg" -> "jpg"
        "image/png" -> "png"
        "image/webp" -> "webp"
        else -> "bin"
    }

    private fun parseDetectResponse(json: String): DetectResponse {
        val root = JSONObject(json)
        val w = root.getInt("imageWidth")
        val h = root.getInt("imageHeight")
        val format = root.getString("imageFormat")

        val detectionsJson = root.optJSONArray("detections") ?: JSONArray()
        val detections = buildList {
            for (i in 0 until detectionsJson.length()) {
                val d = detectionsJson.getJSONObject(i)
                val clazz = d.getString("clazz")
                val conf = d.getDouble("confidence")

                val b = d.getJSONObject("bbox")
                val bbox = BBox(
                    xMin = b.getInt("xMin"),
                    yMin = b.getInt("yMin"),
                    xMax = b.getInt("xMax"),
                    yMax = b.getInt("yMax")
                )

                add(Detection(clazz = clazz, confidence = conf, bbox = bbox))
            }
        }

        return DetectResponse(
            imageWidth = w,
            imageHeight = h,
            imageFormat = format,
            detections = detections
        )
    }

    private fun prettyJson(json: String): String = runCatching {
        JSONObject(json).toString(2)
    }.getOrElse { json }
}

class HttpFailure(val code: Int, val rawBody: String) : RuntimeException("HTTP $code")