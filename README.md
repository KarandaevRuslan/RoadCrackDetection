<h1 align="center">
  <br>
  <b>RoadCrackDetection</b>
  <br>
</h1>

<!-- Badges (small status labels) --------------------------------------->
![Platform](https://img.shields.io/badge/platform-Android-brightgreen)
![Mobile](https://img.shields.io/badge/mobile-Kotlin-blue)
![UI](https://img.shields.io/badge/UI-Jetpack%20Compose-purple)
![Backend](https://img.shields.io/badge/backend-Spring%20Boot-brightgreen)
![Auth](https://img.shields.io/badge/auth-Firebase-orange)
![ML](https://img.shields.io/badge/ML-YOLO-red)

## Overview
**RoadCrackDetection** is a client-server system for **detecting road cracks** on images.

- The **Android app** (a mobile application running on Android OS) is written in **Kotlin** (a programming language for Android) and uses **Jetpack Compose** (a *declarative* UI toolkit, meaning the UI is described as state → UI output).
- The **backend** (the server-side application that receives requests) is built with **Java Spring Boot** (a Java framework for building server applications).
- The crack detector is a **YOLO model** (*You Only Look Once*, a family of real-time object detection models) launched by a **small Python component** (Python code used to run the model inference).

The system uses a **REST API** (*Representational State Transfer*, an HTTP-style interface built around resources and standard verbs like GET/POST) over **HTTPS** (*HTTP Secure*, HTTP encrypted with TLS certificates).

---

## Key Features
- **Image input sources**:
  - camera photo (image captured by the device camera),
  - gallery/file image (an already saved image).
- **Crack detection** using a trained **YOLO** detector (a model that outputs bounding boxes and confidence scores).
- **Authentication and authorization** via **Firebase Authentication** (a managed identity service by Google):
  - sign in with **Google** (OAuth-based identity provider),
  - sign in with **email + password** (classic credential sign-in).
- **Secure transport** via **HTTPS/TLS** (encryption in transit so network traffic is protected).
- **Upload validation** on the server:
  - **magic bytes** (file signature bytes at the beginning of a file, used to verify the real file type),
  - optional **ClamAV scan** (antivirus scanning) used *only as validation* of incoming files.

---

## Repository Structure
- `MobileApp/` — Android client (Kotlin + Jetpack Compose).
- `Server/` — Spring Boot backend + Python inference launcher.
- `tools/` — automation scripts (small helper programs) including certificate utilities.
- `tools/security/` — certificate tooling (scripts to create/update TLS certificates when needed).
- `template_commands/` — example commands (copy/paste templates).
- `other/` — extra materials.

---

## Downloads
These two files are required for a full server deployment:

1) **Detection model**
- Link: https://drive.google.com/file/d/1yV3CfxLJxuja3cF0HZq4OhF55mBILtA7/view?usp=sharing  
- What it is: `best_1.pt` — a **YOLO weights file** (a file with trained model parameters used during inference).

2) **ClamAV bundle (for validation)**
- Link: https://drive.google.com/file/d/1kS-SzdwvBaiqPAExD1i0zBCbkaFx8DX2/view?usp=sharing  
- What it is: `clamav.zip` — **ClamAV** (antivirus engine) with updated **signature databases** (files containing malware fingerprints).

---

## How It Works (high-level)
1. The Android app authenticates the user with **Firebase Authentication** and obtains an **ID token** (a short-lived signed token proving the user identity).
2. The app sends an image to the backend using a **REST API request** over **HTTPS**.
3. The backend validates the uploaded file:
   - checks **magic bytes** to confirm it is a real image format,
   - optionally scans the file with **ClamAV**.
4. The backend launches YOLO inference via a **Python runner** (a small Python module/script).
5. The backend returns detection results as **JSON** (*JavaScript Object Notation*, a text format for structured data).
6. The Android app renders the results (for example, bounding boxes drawn over the image).

---

## Getting Started

### Prerequisites
- **Android Studio** (IDE — Integrated Development Environment — for Android development).
- **JDK** (Java Development Kit — required to build/run Spring Boot), typically **Java 17+**.
- **Gradle** (build tool used by Android and often by Spring Boot projects).
- **Python 3.x** (runtime for the YOLO inference runner).
- Ability to run **HTTPS/TLS** certificates (certificate files used to enable encrypted connections).

### 1) Backend (Spring Boot)
1. Go to the server folder:
   ```bash
   cd Server

2. Configure HTTPS:

   * If you **do not have a domain name** and you use a changing IP address, you may need to **re-generate certificates** after each IP change.
   * Use the scripts in `tools/security/` (certificate tooling) to generate/update certificates and place them where the server expects them.

3. Provide the YOLO weights file:

   * Download `best_1.pt` and put it into the model path used by the server (see server configuration files).

4. Start the Spring Boot server (choose the command used by your project):

   ```bash
   # Gradle wrapper (project-local Gradle)
   ./gradlew bootRun

   # or build a JAR (Java ARchive — a packaged Java app) and run it
   ./gradlew build
   java -jar build/libs/*.jar
   ```

> The exact config keys (like `server.port`, keystore path, model path) depend on your `application.yml` / `application.properties` (Spring Boot configuration files).

### 2) Python YOLO runner (inference component)

* The server uses a **small Python part** to run YOLO inference.
* Install Python dependencies (libraries) as described in `Server/python-yolo` (typically a `requirements.txt` file).

Example (if you have `requirements.txt`):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> “Inference” means running a trained model to get predictions.

### 3) Firebase Authentication (mobile + server)

You typically need:

* Android client config (often `google-services.json` — Firebase Android configuration file).
* Server-side validation of Firebase tokens (the backend verifies the ID token signature and claims).

Make sure:

* The Android app sends the Firebase **ID token** in API requests (usually in `Authorization: Bearer <token>` header).
* The backend validates this token before allowing detection calls.

### 4) Android App (Kotlin + Jetpack Compose)

1. Open `MobileApp/` in Android Studio.
2. Set the backend **base URL** (the root server URL used for API calls), for example:

   * `https://<your-domain>/...` if you have a domain,
   * `https://<your-ip>/...` if you use an IP (and then manage certificates accordingly).
3. Build and run on a device/emulator.

---

## API (conceptual)

Your backend is a **REST API** over **HTTPS**. Common patterns are:

* `POST /.../detect` — upload an image and get crack detections.
* Uses **JWT-like** tokens (Firebase ID token is a signed token similar in usage to a JWT — JSON Web Token).

> For the *exact* endpoint paths and request/response schema, see the Spring Boot controller classes in `Server/`
> (a controller is a class annotated with `@RestController` that defines REST endpoints).

---

## Dataset & Training

The detector was trained using **YOLO training** (the training pipeline for YOLO models).

Please document here:

* **Dataset name** (the source of your training images),
* number of images,
* annotation format (**YOLO format** usually means one `.txt` label file per image with normalized bounding boxes),
* train/validation split (how you separated data for training and evaluation),
* augmentation (transformations like flip/rotate/brightness used to improve generalization).

Template you can fill in:

* Dataset: `TODO`
* Images: `TODO`
* Classes: `TODO` (a “class” is a label category like `crack`)
* Label format: YOLO (`class_id x_center y_center width height`)
* YOLO version: `TODO` (e.g., YOLOv8, YOLOv5, etc.)

---

## Security Notes

* **HTTPS/TLS** protects data in transit (prevents easy interception on the network).
* If you run by IP without a stable domain, certificate renewal can be required after an IP change.
* **Magic bytes validation** helps prevent “fake images” (files renamed to look like `.jpg`/`.png`).
* Optional **ClamAV validation** adds another layer for rejecting suspicious uploads.

---

## Roadmap

* Clear API documentation (OpenAPI/Swagger — machine-readable API spec).
* Better result visualization (confidence filtering, UI overlays).
* Performance improvements (batching requests, caching).
* CI pipeline (Continuous Integration — automated build/test on each commit).

---

## Contributing

1. Fork the repo (create your own copy on GitHub).
2. Create a feature branch (a separate line of development):

   ```bash
   git checkout -b feature/my-change
   ```
3. Open a Pull Request (PR — a request to merge changes into main).

---

## License

Add a `LICENSE` file to define usage terms (MIT/Apache-2.0/GPL, etc.).
