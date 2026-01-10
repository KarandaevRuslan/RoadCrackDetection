package com.karandaev.roadCrackDetector

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController

private object Routes {
    const val Auth = "auth"
    const val Detect = "detect"
    const val Profile = "profile"
}

@Composable
fun App(vm: AuthViewModel = viewModel()) {
    val nav = rememberNavController()
    val state by vm.state.collectAsState()

    val snackbarHostState = remember { SnackbarHostState() }
    val googleClient = rememberGoogleSignInClient()

    LaunchedEffect(state.message) {
        val msg = state.message ?: return@LaunchedEffect
        snackbarHostState.showSnackbar(message = msg.text)
        vm.consumeMessage()
    }

    LaunchedEffect(state.isSignedIn) {
        val target = if (state.isSignedIn) Routes.Detect else Routes.Auth
        nav.navigate(target) {
            popUpTo(nav.graph.id) { inclusive = true }
            launchSingleTop = true
        }
    }

    MaterialTheme {
        Scaffold(
            snackbarHost = { SnackbarHost(hostState = snackbarHostState) }
        ) {
            Box(Modifier.statusBarsPadding()) {
                NavHost(
                    navController = nav,
                    startDestination = if (state.isSignedIn) Routes.Detect else Routes.Auth
                ) {
                    composable(Routes.Auth) {
                        AuthScreen(state = state, vm = vm, googleClient = googleClient)
                    }
                    composable(Routes.Detect) {
                        DetectScreen(
                            state = state,
                            vm = vm,
                            onOpenProfile = { nav.navigate(Routes.Profile) }
                        )
                    }
                    composable(Routes.Profile) {
                        ProfileScreen(
                            state = state,
                            vm = vm,
                            googleClient = googleClient,
                            onBack = { nav.popBackStack() }
                        )
                    }
                }
            }
        }
    }
}