package com.karandaev.roadCrackDetectionServer.image.antivirus;

import com.karandaev.roadCrackDetectionServer.image.ImageValidationException;
import org.springframework.http.HttpStatus;

import java.io.*;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;

public class ClamAvVirusScanner implements VirusScanner {

  private final String host;
  private final int port;
  private final int timeoutMs;

  public ClamAvVirusScanner(String host, int port, int timeoutMs) {
    this.host = host;
    this.port = port;
    this.timeoutMs = timeoutMs;
  }

  @Override
  public void scanOrThrow(byte[] bytes) {
    // clamd protocol: zINSTREAM\0 + chunks (len + data) + 0-len + response line
    try (Socket socket = new Socket()) {
      socket.connect(new InetSocketAddress(host, port), timeoutMs);
      socket.setSoTimeout(timeoutMs);

      OutputStream out = socket.getOutputStream();
      InputStream in = socket.getInputStream();

      out.write("zINSTREAM\0".getBytes(StandardCharsets.US_ASCII));

      int offset = 0;
      int chunkSize = 8192;
      while (offset < bytes.length) {
        int len = Math.min(chunkSize, bytes.length - offset);
        out.write(ByteBuffer.allocate(4).putInt(len).array());
        out.write(bytes, offset, len);
        offset += len;
      }

      // zero-length chunk = end
      out.write(ByteBuffer.allocate(4).putInt(0).array());
      out.flush();

      String resp = readLine(in);
      // Пример: "stream: OK" или "stream: Eicar-Test-Signature FOUND"
      if (resp == null) {
        throw new ImageValidationException(HttpStatus.BAD_GATEWAY, "Antivirus no response");
      }
      if (resp.contains("FOUND")) {
        throw new ImageValidationException(
            HttpStatus.UNSUPPORTED_MEDIA_TYPE, "Malicious content detected");
      }
      if (!resp.contains("OK")) {
        throw new ImageValidationException(HttpStatus.BAD_GATEWAY, "Antivirus error: " + resp);
      }
    } catch (IOException e) {
      throw new ImageValidationException(HttpStatus.BAD_GATEWAY, "Antivirus unavailable");
    }
  }

  private String readLine(InputStream in) throws IOException {
    ByteArrayOutputStream buf = new ByteArrayOutputStream();
    int b;
    while ((b = in.read()) != -1) {
      if (b == '\n') break;
      buf.write(b);
    }
    if (buf.size() == 0 && b == -1) return null;
    return buf.toString(StandardCharsets.UTF_8);
  }
}
