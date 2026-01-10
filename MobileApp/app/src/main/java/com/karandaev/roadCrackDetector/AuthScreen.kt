package com.karandaev.roadCrackDetector

import android.app.Activity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.google.android.gms.auth.api.signin.GoogleSignInClient
import com.google.android.gms.common.api.ApiException

@Composable
fun AuthScreen(
    state: UiState,
    vm: AuthViewModel,
    googleClient: GoogleSignInClient
) {
    val googleLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode != Activity.RESULT_OK) {
            vm.showInfo("Google sign-in was cancelled.")
            return@rememberLauncherForActivityResult
        }

        val data = result.data
        val task =
            com.google.android.gms.auth.api.signin.GoogleSignIn.getSignedInAccountFromIntent(data)

        runCatching {
            task.getResult(ApiException::class.java)
        }.onSuccess { account ->
            val idToken = account.idToken
            if (idToken == null) {
                vm.showError("Google sign-in did not return an ID token.")
            } else {
                vm.signInWithGoogle(idToken)
            }
        }.onFailure { e ->
            vm.showError("Google sign-in failed: ${e.message ?: "Unknown error"}")
        }
    }

    Column(
        Modifier
            .padding(16.dp)
            .fillMaxSize(),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text("Authentication", style = MaterialTheme.typography.headlineSmall)

        OutlinedTextField(
            value = state.email,
            onValueChange = vm::setEmail,
            label = { Text("Email") },
            modifier = Modifier.fillMaxWidth(),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email)
        )

        OutlinedTextField(
            value = state.password,
            onValueChange = vm::setPassword,
            label = { Text("Password") },
            modifier = Modifier.fillMaxWidth(),
            visualTransformation = PasswordVisualTransformation(),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password)
        )

        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Button(onClick = vm::login, enabled = !state.isLoading) {
                Text("Sign in")
            }
            OutlinedButton(onClick = vm::register, enabled = !state.isLoading) {
                Text("Sign up")
            }
        }

        TextButton(
            onClick = vm::sendPasswordResetEmail,
            enabled = !state.isLoading
        ) {
            Text("Forgot password? Send reset email")
        }

        Divider()

        OutlinedButton(
            onClick = { googleLauncher.launch(googleClient.signInIntent) },
            enabled = !state.isLoading,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Continue with Google")
        }

        if (state.isLoading) {
            CircularProgressIndicator()
        }
    }
}
