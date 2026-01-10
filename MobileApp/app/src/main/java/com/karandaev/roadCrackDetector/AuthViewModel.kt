package com.karandaev.roadCrackDetector

import com.karandaev.roadCrackDetector.api.DetectRepository
import com.karandaev.roadCrackDetector.api.HttpFailure

import android.content.Context
import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseAuthException
import com.google.firebase.auth.FirebaseUser
import com.google.firebase.auth.GoogleAuthProvider
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await

data class UserProfile(
    val uid: String,
    val email: String?,
    val displayName: String?,
    val photoUrl: String?,
    val emailVerified: Boolean,
    val providerIds: List<String>
)

data class UiMessage(val text: String)

data class UiState(
    val email: String = "",
    val password: String = "",
    val isLoading: Boolean = false,
    val message: UiMessage? = null,

    val isSignedIn: Boolean = false,
    val profile: UserProfile? = null,

    // Detect screen state
    val selectedImageUri: String? = null,
    val detectResponse: DetectResponse? = null,
    val detectPrettyJson: String? = null
)

class AuthViewModel(
    private val auth: FirebaseAuth = FirebaseAuth.getInstance(),
    private val detectRepo: DetectRepository = DetectRepository(
        auth = auth,
        baseUrl = ApiConfig.baseUrl
    )
) : ViewModel() {

    private val _state = MutableStateFlow(
        UiState(
            isSignedIn = auth.currentUser != null,
            profile = auth.currentUser?.toProfile()
        )
    )
    val state: StateFlow<UiState> = _state

    private val authListener = FirebaseAuth.AuthStateListener { firebaseAuth ->
        val user = firebaseAuth.currentUser
        _state.update {
            it.copy(
                isSignedIn = user != null,
                profile = user?.toProfile()
            )
        }
    }

    init {
        auth.addAuthStateListener(authListener)
    }

    override fun onCleared() {
        auth.removeAuthStateListener(authListener)
        super.onCleared()
    }

    fun consumeMessage() {
        _state.update { it.copy(message = null) }
    }

    fun showInfo(text: String) {
        _state.update { it.copy(message = UiMessage(text)) }
    }

    fun showError(text: String) {
        _state.update { it.copy(message = UiMessage(text)) }
    }

    fun setEmail(value: String) {
        _state.update { it.copy(email = value) }
    }

    fun setPassword(value: String) {
        _state.update { it.copy(password = value) }
    }

    // --- Email auth ---

    fun register() = viewModelScope.launch {
        runCatching {
            setLoading(true)

            val email = _state.value.email.trim()
            val password = _state.value.password

            require(email.isNotBlank()) { "Please enter your email address." }
            require(password.isNotBlank()) { "Please enter your password." }

            auth.createUserWithEmailAndPassword(email, password).await()

            val user = auth.currentUser ?: error("No current user")
            user.sendEmailVerification().await()

            auth.signOut()
            showInfo("Verification email sent to $email. Please verify your email, then sign in.")
        }.onFailure { e ->
            showError(friendlyAuthMessage(e))
        }
        setLoading(false)
    }

    fun login() = viewModelScope.launch {
        runCatching {
            setLoading(true)

            val email = _state.value.email.trim()
            val password = _state.value.password

            require(email.isNotBlank()) { "Please enter your email address." }
            require(password.isNotBlank()) { "Please enter your password." }

            auth.signInWithEmailAndPassword(email, password).await()

            val user = auth.currentUser ?: error("No current user")
            user.reload().await()

            if (!user.isEmailVerified) {
                user.sendEmailVerification().await()
                auth.signOut()
                showInfo("Your email is not verified yet. We sent a verification email to $email. Please verify it and try again.")
                return@runCatching
            }

            showInfo("Signed in successfully.")
        }.onFailure { e ->
            showError(friendlyAuthMessage(e))
        }
        setLoading(false)
    }

    fun sendPasswordResetEmail() = viewModelScope.launch {
        runCatching {
            setLoading(true)

            val email = _state.value.email.trim()
            require(email.isNotBlank()) { "Please enter your email address first." }

            auth.sendPasswordResetEmail(email).await()
            showInfo("Password reset email sent to $email. Please check your inbox.")
        }.onFailure { e ->
            showError(friendlyAuthMessage(e))
        }
        setLoading(false)
    }

    // --- Google auth ---

    fun signInWithGoogle(idToken: String) = viewModelScope.launch {
        runCatching {
            setLoading(true)
            val credential = GoogleAuthProvider.getCredential(idToken, null)
            auth.signInWithCredential(credential).await()
            showInfo("Signed in with Google successfully.")
        }.onFailure { e ->
            showError(friendlyAuthMessage(e))
        }
        setLoading(false)
    }

    // --- Detect flow ---

    fun setSelectedImage(uri: Uri?) {
        _state.update {
            it.copy(
                selectedImageUri = uri?.toString(),
                detectResponse = null,
                detectPrettyJson = null
            )
        }
    }

    fun clearSelectedImage() {
        setSelectedImage(null)
    }

    fun detectSelectedImage(context: Context) = viewModelScope.launch {
        val uriString = _state.value.selectedImageUri
        if (uriString.isNullOrBlank()) {
            showInfo("Please select an image first.")
            return@launch
        }

        runCatching {
            setLoading(true)

            val (resp, pretty) = detectRepo.detect(context, Uri.parse(uriString))

            _state.update {
                it.copy(
                    detectResponse = resp,
                    detectPrettyJson = pretty
                )
            }

            showInfo("Detection completed.")
        }.onFailure { e ->
            showError(friendlyDetectMessage(e))
        }

        setLoading(false)
    }

    // --- Logout ---

    fun logout(externalSignOut: suspend () -> Unit = {}) = viewModelScope.launch {
        runCatching {
            setLoading(true)
            externalSignOut()
            auth.signOut()
            _state.value = UiState(isSignedIn = false)
            showInfo("You have been signed out.")
        }.onFailure { e ->
            auth.signOut()
            _state.value = UiState(isSignedIn = false)
            showError("Signed out, but an external provider sign-out step failed. ${e.message ?: ""}".trim())
        }
        setLoading(false)
    }

    private fun setLoading(isLoading: Boolean) {
        _state.update { it.copy(isLoading = isLoading) }
    }

    private fun friendlyAuthMessage(t: Throwable): String {
        val authEx = t as? FirebaseAuthException
        return when (authEx?.errorCode) {
            "ERROR_INVALID_EMAIL" -> "The email address is not valid."
            "ERROR_USER_NOT_FOUND" -> "No account found for this email."
            "ERROR_WRONG_PASSWORD" -> "Incorrect password. Please try again."
            "ERROR_EMAIL_ALREADY_IN_USE" -> "This email is already registered. Try signing in instead."
            "ERROR_WEAK_PASSWORD" -> "Password is too weak. Please use at least 6 characters."
            "ERROR_TOO_MANY_REQUESTS" -> "Too many attempts. Please wait a bit and try again."
            "ERROR_NETWORK_REQUEST_FAILED" -> "Network error. Please check your internet connection."
            else -> t.message ?: "Something went wrong. Please try again."
        }
    }

    private fun friendlyDetectMessage(t: Throwable): String {
        if (t is IllegalArgumentException) return t.message ?: "Invalid image."

        if (t is HttpFailure) {
            return when (t.code) {
                400 -> "The image looks invalid. Please try another image."
                401, 403 -> "You are not authorized. Please sign in again."
                413 -> "Image is too large. Max size is 10 MB."
                415 -> "Unsupported image format. Please use JPEG, PNG, or WEBP."
                else -> "Detection failed (HTTP ${t.code}). Please try again."
            }
        }

        return t.message ?: "Detection failed. Please try again."
    }
}

private fun FirebaseUser.toProfile(): UserProfile {
    val providers = providerData
        .mapNotNull { it.providerId }
        .filter { it.isNotBlank() }
        .distinct()

    return UserProfile(
        uid = uid,
        email = email,
        displayName = displayName,
        photoUrl = photoUrl?.toString(),
        emailVerified = isEmailVerified,
        providerIds = providers
    )
}

object ApiConfig {
    const val baseUrl: String = BuildConfig.API_BASE_URL;
}
