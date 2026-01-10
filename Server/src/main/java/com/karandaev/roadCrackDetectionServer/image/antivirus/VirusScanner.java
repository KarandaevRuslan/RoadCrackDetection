package com.karandaev.roadCrackDetectionServer.image.antivirus;

public interface VirusScanner {
  void scanOrThrow(byte[] bytes);
}
