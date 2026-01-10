package com.karandaev.roadCrackDetectionServer.ratelimit;

import io.github.bucket4j.Bucket;
import io.github.bucket4j.ConsumptionProbe;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.MediaType;
import org.springframework.web.filter.OncePerRequestFilter;
import org.jetbrains.annotations.NotNull;

import java.io.IOException;

public class RateLimitingFilter extends OncePerRequestFilter {

  private final RateLimitProperties props;
  private final RateLimiterService service;
  private final RateLimitKeyResolver keyResolver = new RateLimitKeyResolver();
  private final RateLimitRuleResolver ruleResolver;

  public RateLimitingFilter(RateLimitProperties props, RateLimiterService service) {
    this.props = props;
    this.service = service;
    this.ruleResolver = new RateLimitRuleResolver(props);
  }

  @Override
  protected void doFilterInternal(
      @NotNull HttpServletRequest request,
      @NotNull HttpServletResponse response,
      @NotNull FilterChain filterChain)
      throws ServletException, IOException {

    if (!props.isEnabled()) {
      filterChain.doFilter(request, response);
      return;
    }

    var rule = ruleResolver.resolve(request);
    if (rule == null) {
      filterChain.doFilter(request, response);
      return;
    }

    var key = keyResolver.resolve(request);

    var limits = service.buildLimits(rule, key.authenticated());
    if (limits.isEmpty()) {
      filterChain.doFilter(request, response);
      return;
    }

    String cacheKey = rule.getId() + "|" + key.value();
    Bucket bucket = service.bucketFor(cacheKey, limits);

    int cost = Math.max(1, rule.getCost());
    ConsumptionProbe probe = bucket.tryConsumeAndReturnRemaining(cost);

    // Заголовки для дебага/клиента (не обязательны, но полезны)
    response.setHeader("X-RateLimit-Rule", rule.getId());
    response.setHeader("X-RateLimit-Key", key.authenticated() ? "uid" : "ip");
    response.setHeader("X-RateLimit-Remaining", String.valueOf(probe.getRemainingTokens()));

    if (probe.isConsumed()) {
      filterChain.doFilter(request, response);
      return;
    }

    // 429 Too Many Requests
    long waitNanos = probe.getNanosToWaitForRefill();
    long waitSeconds = Math.max(1, waitNanos / 1_000_000_000L);

    response.setStatus(429);
    response.setHeader("Retry-After", String.valueOf(waitSeconds)); // стандартный заголовок
    response.setContentType(MediaType.APPLICATION_JSON_VALUE);
    response
        .getWriter()
        .write(
            """
        {"error":"rate_limited","message":"Too many requests. Try later."}
        """);
  }
}
