package com.karandaev.roadCrackDetectionServer.image;

import java.util.Optional;

public final class MagicBytesSniffer {

  public enum Format {
    JPEG("JPEG"),
    PNG("PNG"),
    WEBP("WEBP"),
    GIF("GIF"),
    BMP("BMP");

    private final String imageIoName;

    Format(String imageIoName) {
      this.imageIoName = imageIoName;
    }

    public String imageIoName() {
      return imageIoName;
    }
  }

  public Optional<Format> sniff(byte[] bytes) {
    if (bytes == null || bytes.length < 12) return Optional.empty();

    // PNG: 89 50 4E 47 0D 0A 1A 0A
    if (startsWith(bytes, new byte[] {(byte) 0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A})) {
      return Optional.of(Format.PNG);
    }

    // JPEG: FF D8 ... FF D9 (конец может быть не проверяем, но начало обязано)
    if ((bytes[0] & 0xFF) == 0xFF && (bytes[1] & 0xFF) == 0xD8) {
      return Optional.of(Format.JPEG);
    }

    // WEBP: "RIFF" .... "WEBP"
    if (bytes[0] == 'R'
        && bytes[1] == 'I'
        && bytes[2] == 'F'
        && bytes[3] == 'F'
        && bytes[8] == 'W'
        && bytes[9] == 'E'
        && bytes[10] == 'B'
        && bytes[11] == 'P') {
      return Optional.of(Format.WEBP);
    }

    // GIF: "GIF87a" or "GIF89a"
    if (bytes[0] == 'G'
        && bytes[1] == 'I'
        && bytes[2] == 'F'
        && bytes[3] == '8'
        && (bytes[4] == '7' || bytes[4] == '9')
        && bytes[5] == 'a') {
      return Optional.of(Format.GIF);
    }

    // BMP: "BM"
    if (bytes[0] == 'B' && bytes[1] == 'M') {
      return Optional.of(Format.BMP);
    }

    return Optional.empty();
  }

  private boolean startsWith(byte[] data, byte[] prefix) {
    if (data.length < prefix.length) return false;
    for (int i = 0; i < prefix.length; i++) {
      if (data[i] != prefix[i]) return false;
    }
    return true;
  }
}
