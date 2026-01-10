package com.karandaev.roadCrackDetectionServer.security;

import com.google.auth.oauth2.GoogleCredentials;
import com.google.firebase.FirebaseApp;
import com.google.firebase.FirebaseOptions;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.Resource;

import jakarta.annotation.PostConstruct;
import java.io.IOException;
import java.io.InputStream;

@Configuration
public class FirebaseConfig {

  @Value("${firebase.service-account}")
  private Resource serviceAccount;

  @PostConstruct
  public void init() throws IOException {
    // Не создаём второй раз, если приложение уже инициализировано
    if (!FirebaseApp.getApps().isEmpty()) return;

    try (InputStream in = serviceAccount.getInputStream()) {
      FirebaseOptions options =
          FirebaseOptions.builder().setCredentials(GoogleCredentials.fromStream(in)).build();

      FirebaseApp.initializeApp(options);
    }
  }
}
