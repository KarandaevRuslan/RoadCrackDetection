package com.karandaev.roadCrackDetectionServer.ratelimit;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;

import java.util.ArrayList;
import java.util.List;

@Setter
@Getter
@ConfigurationProperties(prefix = "rate-limit")
public class RateLimitProperties {

  private boolean enabled = true;
  private int cacheTtlMinutes = 60;

  private List<Rule> rules = new ArrayList<>();

  @Setter
  @Getter
  public static class Limit {
    private int capacity;
    private int refillTokens;
    private int refillPeriodSeconds;
  }

  @Setter
  @Getter
  public static class Rule {
    private String id;
    private String method = "ANY"; // GET/POST/... или ANY
    private String path; // pattern
    private int cost = 1;

    private Limit user;
    private Limit ip;

    // опциональный лимит "per second"
    private Limit userPerSecond;
  }
}
