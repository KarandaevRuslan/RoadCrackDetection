package com.karandaev.roadCrackDetectionServer.errors;

import com.karandaev.roadCrackDetectionServer.image.ImageValidationException;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.Map;

@RestControllerAdvice
public class GlobalExceptionHandler {

  @ExceptionHandler(BadCredentialsException.class)
  public ResponseEntity<?> badCredentials(BadCredentialsException ex) {
    return ResponseEntity.status(401)
        .body(Map.of("error", "unauthorized", "message", ex.getMessage()));
  }

  @ExceptionHandler(ImageValidationException.class)
  public ResponseEntity<?> imageValidation(ImageValidationException ex) {
    return ResponseEntity.status(ex.getStatus())
        .body(Map.of("error", "invalid_image", "message", ex.getMessage()));
  }
}
