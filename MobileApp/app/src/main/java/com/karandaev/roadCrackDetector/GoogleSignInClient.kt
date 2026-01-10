package com.karandaev.roadCrackDetector

import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.google.android.gms.auth.api.signin.GoogleSignInClient
import com.google.android.gms.auth.api.signin.GoogleSignInOptions

@Composable
fun rememberGoogleSignInClient(): GoogleSignInClient {
    val context = LocalContext.current

    // default_web_client_id is generated from google-services.json by the google-services plugin
    val webClientId = context.getString(R.string.default_web_client_id)

    return remember(webClientId) {
        val gso = GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
            .requestIdToken(webClientId)
            .requestEmail()
            .build()

        GoogleSignIn.getClient(context, gso)
    }
}
