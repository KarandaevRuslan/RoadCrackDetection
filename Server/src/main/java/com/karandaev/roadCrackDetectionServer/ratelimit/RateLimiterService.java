package com.karandaev.roadCrackDetectionServer.ratelimit;

import io.github.bucket4j.Bandwidth;
import io.github.bucket4j.Bucket;
import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

public class RateLimiterService {

  private final Cache<String, Bucket> buckets;

  public RateLimiterService(RateLimitProperties props) {
    this.buckets =
        Caffeine.newBuilder()
            .expireAfterAccess(Duration.ofMinutes(props.getCacheTtlMinutes()))
            .maximumSize(200_000)
            .build();
  }

  public Bucket bucketFor(String cacheKey, List<Bandwidth> limits) {
    if (limits == null || limits.isEmpty()) {
      return null; // или другой вариант: "не лимитируем"
    }

    return buckets.get(
        cacheKey,
        k -> {
          var builder = Bucket.builder();
          for (Bandwidth bw : limits) {
            builder.addLimit(bw);
          }
          return builder.build();
        });
  }

  public List<Bandwidth> buildLimits(RateLimitProperties.Rule rule, boolean authenticated) {
    var base = authenticated ? rule.getUser() : rule.getIp();
    if (base == null) {
      // если не задано - значит не лимитируем
      return List.of();
    }

    List<Bandwidth> limits = new ArrayList<>();
    limits.add(toBandwidth(base));

    // Доп. лимит "per second" применяем только для user (можно расширить и на ip)
    if (authenticated && rule.getUserPerSecond() != null) {
      limits.add(toBandwidth(rule.getUserPerSecond()));
    }

    return limits;
  }

  private Bandwidth toBandwidth(RateLimitProperties.Limit limit) {
    return Bandwidth.builder()
        .capacity(limit.getCapacity())
        .refillIntervally(
            limit.getRefillTokens(), Duration.ofSeconds(limit.getRefillPeriodSeconds()))
        .build();
  }
}
