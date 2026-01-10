package com.karandaev.roadCrackDetectionServer.image;

import lombok.Getter;
import org.springframework.http.HttpStatus;

@Getter
public class ImageValidationException extends RuntimeException {
  private final HttpStatus status;

  public ImageValidationException(HttpStatus status, String message) {
    super(message);
    this.status = status;
  }
}
