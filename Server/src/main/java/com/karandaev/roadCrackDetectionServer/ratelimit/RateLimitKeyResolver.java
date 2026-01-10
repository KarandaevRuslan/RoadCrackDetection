package com.karandaev.roadCrackDetectionServer.ratelimit;

import com.karandaev.roadCrackDetectionServer.security.FirebasePrincipal;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

public class RateLimitKeyResolver {

  public record Key(boolean authenticated, String value) {}

  public Key resolve(HttpServletRequest request) {
    Authentication auth = SecurityContextHolder.getContext().getAuthentication();
    if (auth != null
        && auth.isAuthenticated()
        && auth.getPrincipal() instanceof FirebasePrincipal fp) {
      return new Key(true, "uid:" + fp.uid());
    }

    // IP: если есть reverse proxy (например Nginx), часто передает X-Forwarded-For
    String xff = request.getHeader("X-Forwarded-For");
    String ip =
        (xff != null && !xff.isBlank()) ? xff.split(",")[0].trim() : request.getRemoteAddr();

    return new Key(false, "ip:" + ip);
  }
}
