package com.karandaev.roadCrackDetectionServer.yolo.process;

import com.karandaev.roadCrackDetectionServer.util.ProcessOutputGobbler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.SmartLifecycle;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.io.File;
import java.time.Instant;
import java.util.ArrayList;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

@Component
public class YoloProcessManager implements SmartLifecycle {
  private static final Logger log = LoggerFactory.getLogger(YoloProcessManager.class);

  private final YoloProcessProperties props;
  private volatile boolean running = false;

  private Process process;
  private Future<?> stdoutTask;
  private Future<?> stderrTask;

  public YoloProcessManager(YoloProcessProperties props) {
    this.props = props;
  }

  @Override
  public void start() {
    if (!props.isEnabled()) {
      log.info("YOLO process manager disabled");
      running = true;
      return;
    }
    if (running) return;

    try {
      startProcess();
      waitForHealth();
      running = true;
      log.info("YOLO python process is up");
    } catch (Exception e) {
      stopProcessHard();
      throw new IllegalStateException("Failed to start YOLO python service: " + e.getMessage(), e);
    }
  }

  private void startProcess() throws Exception {
    File workdir = new File(props.getWorkdir());
    if (!workdir.isDirectory()) {
      throw new IllegalStateException("workdir not found: " + workdir.getAbsolutePath());
    }

    if (props.getPythonExe() == null || props.getPythonExe().isBlank()) {
      throw new IllegalStateException("python-exe is not set");
    }

    String pythonExe =
        props.getPythonExe().trim().replace("/", File.separator).replace("\\", File.separator);

    File pythonFile = new File(workdir, pythonExe);

    log.info("pythonFile abs={}", pythonFile.getAbsolutePath());
    log.info("pythonFile exists={}", pythonFile.isFile());

    if (!pythonFile.isFile()) {
      throw new IllegalStateException("python.exe not found: " + pythonFile.getAbsolutePath());
    }

    var cmd = new ArrayList<String>();
    cmd.add(pythonFile.getAbsolutePath());
    if (props.getArgs() != null) cmd.addAll(props.getArgs());

    ProcessBuilder pb = new ProcessBuilder(cmd);
    pb.directory(workdir);
    pb.redirectErrorStream(false);

    log.info(
        "Starting YOLO python process: workdir={}, cmd={}",
        workdir.getAbsolutePath(),
        String.join(" ", cmd));

    process = pb.start();

    var pool = Executors.newFixedThreadPool(2);
    stdoutTask =
        pool.submit(new ProcessOutputGobbler(process.getInputStream(), log, "[py-stdout] "));
    stderrTask =
        pool.submit(new ProcessOutputGobbler(process.getErrorStream(), log, "[py-stderr] "));
  }

  private void waitForHealth() {
    // RestTemplate (HTTP клиент Spring) - простой клиент, чтобы пинговать /health
    SimpleClientHttpRequestFactory f = new SimpleClientHttpRequestFactory();
    f.setConnectTimeout(1000);
    f.setReadTimeout(1000);
    RestTemplate rt = new RestTemplate(f);

    Instant deadline = Instant.now().plusMillis(props.getStartupTimeoutMs());

    while (Instant.now().isBefore(deadline)) {
      // Если процесс уже умер - не ждём дальше
      if (process != null && !process.isAlive()) {
        int code = process.exitValue();
        throw new IllegalStateException("Python process exited early with code " + code);
      }

      try {
        var resp = rt.getForEntity(props.getHealthUrl(), String.class);
        if (resp.getStatusCode().is2xxSuccessful()) return;
      } catch (Exception ignored) {
        // сервис ещё не поднялся
      }

      try {
        Thread.sleep(200);
      } catch (InterruptedException ie) {
        Thread.currentThread().interrupt();
        throw new IllegalStateException("Interrupted while waiting for health");
      }
    }

    throw new IllegalStateException("Health check timeout: " + props.getHealthUrl());
  }

  @Override
  public void stop() {
    if (!props.isEnabled()) {
      running = false;
      return;
    }
    stopProcessGracefully();
    running = false;
  }

  private void stopProcessGracefully() {
    if (process == null) return;

    log.info("Stopping YOLO python process...");
    process.destroy(); // SIGTERM (мягкая остановка на Unix)

    Instant deadline = Instant.now().plusMillis(props.getShutdownTimeoutMs());
    while (process.isAlive() && Instant.now().isBefore(deadline)) {
      try {
        Thread.sleep(100);
      } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
        break;
      }
    }

    if (process.isAlive()) {
      log.warn("YOLO python process did not stop in time, killing...");
      stopProcessHard();
    }
  }

  private void stopProcessHard() {
    try {
      if (process != null && process.isAlive()) {
        process.destroyForcibly(); // SIGKILL (жёсткая остановка на Unix)
      }
    } catch (Exception ignored) {
    }

    process = null;
    if (stdoutTask != null) stdoutTask.cancel(true);
    if (stderrTask != null) stderrTask.cancel(true);
  }

  @Override
  public boolean isRunning() {
    return running;
  }

  @Override
  public int getPhase() {
    // Чем меньше phase, тем раньше стартует. Можно поставить ранний старт.
    return Integer.MIN_VALUE + 1000;
  }

  @Override
  public boolean isAutoStartup() {
    return true;
  }

  @Override
  public void stop(Runnable callback) {
    stop();
    callback.run();
  }
}
