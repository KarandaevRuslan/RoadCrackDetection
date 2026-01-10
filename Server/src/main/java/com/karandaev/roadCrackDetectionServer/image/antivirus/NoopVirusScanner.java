package com.karandaev.roadCrackDetectionServer.image.antivirus;

public class NoopVirusScanner implements VirusScanner {
  @Override
  public void scanOrThrow(byte[] bytes) {
    // intentionally empty
  }
}
