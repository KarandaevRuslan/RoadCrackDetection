package com.karandaev.roadCrackDetectionServer.util;

import org.slf4j.Logger;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.Charset;

/** ProcessOutputGobbler — читает поток процесса построчно и логирует. */
public final class ProcessOutputGobbler implements Runnable {

  private final InputStream in;
  private final Logger log;
  private final String prefix;
  private final Charset charset;

  public ProcessOutputGobbler(InputStream in, Logger log, String prefix) {
    this(in, log, prefix, Charset.defaultCharset());
  }

  public ProcessOutputGobbler(InputStream in, Logger log, String prefix, Charset charset) {
    this.in = in;
    this.log = log;
    this.prefix = prefix;
    this.charset = charset;
  }

  @Override
  public void run() {
    try (BufferedReader br = new BufferedReader(new InputStreamReader(in, charset))) {
      String line;
      while (!Thread.currentThread().isInterrupted() && (line = br.readLine()) != null) {
        log.info("{}{}", prefix, line);
      }
    } catch (Exception e) {
      // Обычно сюда попадаем при остановке процесса/закрытии потока — это не критично.
      log.debug("{}gobbler stopped: {}", prefix, e.toString());
    }
  }
}
