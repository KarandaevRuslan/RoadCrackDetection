package com.karandaev.roadCrackDetector

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import com.google.android.gms.auth.api.signin.GoogleSignInClient
import kotlinx.coroutines.tasks.await

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProfileScreen(
    state: UiState,
    vm: AuthViewModel,
    googleClient: GoogleSignInClient,
    onBack: () -> Unit
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Profile") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            Modifier
                .padding(padding)
                .padding(16.dp)
                .fillMaxSize(),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            state.profile?.let { p ->
                Card {
                    Column(
                        Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        if (!p.photoUrl.isNullOrBlank()) {
                            AsyncImage(
                                model = p.photoUrl,
                                contentDescription = "Profile photo",
                                modifier = Modifier.size(72.dp)
                            )
                        }
                        Text("UID: ${p.uid}")
                        Text("Email: ${p.email ?: "-"}")
                        Text("Display name: ${p.displayName ?: "-"}")
                        Text("Email verified: ${p.emailVerified}")
                        Text("Providers: ${p.providerIds.joinToString()}")
                    }
                }
            } ?: run {
                Text("No profile data.")
            }

            Spacer(Modifier.weight(1f))

            Button(
                onClick = {
                    vm.logout(externalSignOut = { googleClient.signOut().await() })
                },
                enabled = !state.isLoading,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Log out")
            }
        }
    }
}
