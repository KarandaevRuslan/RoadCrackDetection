package com.karandaev.roadCrackDetectionServer.image.antivirus;

import com.karandaev.roadCrackDetectionServer.util.ProcessOutputGobbler;
import jakarta.annotation.PreDestroy;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;

import java.io.File;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.time.Duration;

public class ClamdLifecycle {

  private static final Logger log = LoggerFactory.getLogger(ClamdLifecycle.class);

  private final String clamdExe;
  private final String clamdConf;
  private final String host;
  private final int port;
  private final int startupTimeoutMs;

  private Process clamd;
  private Thread clamdOutThread;

  public ClamdLifecycle(
      String clamdExe, String clamdConf, String host, int port, int startupTimeoutMs) {
    this.clamdExe = clamdExe;
    this.clamdConf = clamdConf;
    this.host = host;
    this.port = port;
    this.startupTimeoutMs = startupTimeoutMs;
  }

  @EventListener(ApplicationReadyEvent.class)
  public void start() throws IOException {
    log.info("Starting clamd. user.dir={}", System.getProperty("user.dir"));

    if (clamdExe == null || clamdExe.isBlank()) {
      throw new IllegalStateException(
          "image-security.antivirus.clamd-exe is required when start-clamd=true");
    }
    if (clamdConf == null || clamdConf.isBlank()) {
      throw new IllegalStateException(
          "image-security.antivirus.clamd-conf is required when start-clamd=true");
    }

    String exe = clamdExe.trim();
    String conf = clamdConf.trim();

    File exeFile = new File(exe);
    File confFile = new File(conf);

    log.info("clamdExeRaw=[{}], len={}", clamdExe, clamdExe.length());
    log.info(
        "clamdExe abs={}, exists={}, isFile={}",
        exeFile.getAbsolutePath(),
        exeFile.exists(),
        exeFile.isFile());

    log.info("clamdConfRaw=[{}], len={}", clamdConf, clamdConf.length());
    log.info(
        "clamdConf abs={}, exists={}, isFile={}",
        confFile.getAbsolutePath(),
        confFile.exists(),
        confFile.isFile());

    if (!exeFile.isFile()) {
      throw new IllegalStateException("clamd exe not found: " + exeFile.getAbsolutePath());
    }
    if (!confFile.isFile()) {
      throw new IllegalStateException("clamd conf not found: " + confFile.getAbsolutePath());
    }

    log.info(
        "Launching clamd: exe={}, -c {}", exeFile.getAbsolutePath(), confFile.getAbsolutePath());

    // redirectErrorStream(true) — stderr (ошибки) объединяем в stdout (вывод)
    clamd =
        new ProcessBuilder(exeFile.getAbsolutePath(), "-c", confFile.getAbsolutePath())
            .redirectErrorStream(true)
            .start();

    try {
      log.info("clamd started. pid={}", clamd.pid());
    } catch (Throwable t) {
      log.info("clamd started. pid=<unavailable>");
    }

    // читаем вывод процесса отдельным потоком
    clamdOutThread =
        new Thread(
            new ProcessOutputGobbler(clamd.getInputStream(), log, "[clamd] "),
            "clamd-output-gobbler");
    clamdOutThread.setDaemon(true);
    clamdOutThread.start();

    waitForTcpPort(host, port, Duration.ofMillis(startupTimeoutMs), clamd);

    log.info("clamd is reachable on {}:{}", host, port);
  }

  @PreDestroy
  public void stop() {
    log.info("Stopping clamd...");
    if (clamd != null && clamd.isAlive()) {
      clamd.destroy();
      log.info("clamd destroy() sent");
    }
    if (clamdOutThread != null) {
      clamdOutThread.interrupt();
    }
  }

  private static void waitForTcpPort(String host, int port, Duration timeout, Process proc) {
    long end = System.currentTimeMillis() + timeout.toMillis();

    while (System.currentTimeMillis() < end) {
      // isAlive() — жив ли процесс
      if (proc != null && !proc.isAlive()) {
        int code = proc.exitValue(); // exitValue — код завершения
        throw new IllegalStateException("clamd exited early with code " + code);
      }

      try (Socket s = new Socket()) {
        // connect(...) — попытка подключиться к TCP порту
        s.connect(new InetSocketAddress(host, port), 500);
        return;
      } catch (Exception ignored) {
        try {
          Thread.sleep(200);
        } catch (InterruptedException e) {
          Thread.currentThread().interrupt();
          throw new IllegalStateException("Interrupted while waiting for clamd TCP port");
        }
      }
    }

    throw new IllegalStateException(
        "clamd did not open " + host + ":" + port + " within " + timeout);
  }
}
