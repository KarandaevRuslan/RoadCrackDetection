package com.karandaev.roadCrackDetector

import android.Manifest
import android.content.Context
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AccountCircle
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import java.io.File

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DetectScreen(
    state: UiState,
    vm: AuthViewModel,
    onOpenProfile: () -> Unit
) {
    val context = LocalContext.current

    // Uri = a reference to a file/content in Android (not necessarily a file path).
    var pendingCameraUri by remember { mutableStateOf<Uri?>(null) }

    // Launcher = a remembered object that starts an Android system flow and returns a result.
    val pickImage = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent() // GetContent = system picker for a file (here: image)
    ) { uri ->
        if (uri == null) vm.showInfo("No image selected.")
        else vm.setSelectedImage(uri)
    }

    // IMPORTANT: declare takePhoto BEFORE requestCameraPermission (so it exists).
    val takePhoto = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.TakePicture() // TakePicture = camera app writes photo into a provided Uri
    ) { success ->
        val uri = pendingCameraUri
        if (!success || uri == null) {
            vm.showInfo("Camera capture was cancelled.")
        } else {
            vm.setSelectedImage(uri)
        }
    }

    val requestCameraPermission = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission() // RequestPermission = asks user for runtime permission
    ) { granted ->
        if (!granted) {
            vm.showInfo("Camera permission is required to take a photo.")
        } else {
            val uri = createTempImageUri(context)
            pendingCameraUri = uri
            takePhoto.launch(uri)
        }
    }

    val selectedUri = state.selectedImageUri?.let(Uri::parse)

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Crack Detection") },
                actions = {
                    IconButton(onClick = onOpenProfile) {
                        Icon(Icons.Default.AccountCircle, contentDescription = "Open profile")
                    }
                }
            )
        }
    ) { padding ->
        val scrollState = rememberScrollState()
        Column(
            Modifier
                .padding(padding)
                .padding(16.dp)
                .fillMaxSize()
                .navigationBarsPadding()
                .verticalScroll(scrollState),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedButton(
                    onClick = { pickImage.launch("image/*") },
                    enabled = !state.isLoading
                ) {
                    Text("Pick image")
                }

                OutlinedButton(
                    onClick = { requestCameraPermission.launch(Manifest.permission.CAMERA) },
                    enabled = !state.isLoading
                ) {
                    Text("Take photo")
                }

                IconButton(
                    onClick = vm::clearSelectedImage,
                    enabled = !state.isLoading && selectedUri != null
                ) {
                    Icon(Icons.Default.Delete, contentDescription = "Clear image")
                }
            }

            Button(
                onClick = { vm.detectSelectedImage(context) },
                enabled = !state.isLoading && selectedUri != null,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Detect")
            }

            if (state.isLoading) {
                CircularProgressIndicator()
            }

            if (selectedUri != null) {
                DetectionPreview(
                    imageUri = selectedUri,
                    response = state.detectResponse
                )
            }

            state.detectResponse?.let { resp ->
                Text("Text result", style = MaterialTheme.typography.titleMedium)

                if (resp.detections.isEmpty()) {
                    Text("No detections found.")
                } else {
                    resp.detections.forEachIndexed { index, d ->
                        Text(
                            "${index + 1}. class=${d.clazz}, confidence=${"%.3f".format(d.confidence)}, " +
                                    "bbox=[${d.bbox.xMin}, ${d.bbox.yMin}, ${d.bbox.xMax}, ${d.bbox.yMax}]"
                        )
                    }
                }

                Spacer(Modifier.height(8.dp))

                Text("Raw response (pretty JSON)", style = MaterialTheme.typography.titleMedium)
                Text(state.detectPrettyJson ?: "")
            }
        }
    }
}

// FileProvider = Android component that safely shares file Uris with other apps (like Camera).
private fun createTempImageUri(context: Context): Uri {
    val file = File(context.cacheDir, "capture_${System.currentTimeMillis()}.jpg")
    return FileProvider.getUriForFile(
        context,
        "${context.packageName}.fileprovider",
        file
    )
}
