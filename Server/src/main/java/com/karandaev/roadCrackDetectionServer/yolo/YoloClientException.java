package com.karandaev.roadCrackDetectionServer.yolo;

public class YoloClientException extends RuntimeException {
  public YoloClientException(String message) {
    super(message);
  }

  public YoloClientException(String message, Throwable cause) {
    super(message, cause);
  }
}
