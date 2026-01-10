package com.karandaev.roadCrackDetectionServer.ratelimit;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.util.AntPathMatcher;

public class RateLimitRuleResolver {

  private final RateLimitProperties props;
  private final AntPathMatcher matcher = new AntPathMatcher();

  public RateLimitRuleResolver(RateLimitProperties props) {
    this.props = props;
  }

  public RateLimitProperties.Rule resolve(HttpServletRequest request) {
    String uri = request.getRequestURI();
    String method = request.getMethod();

    // Правила идут сверху вниз: первое совпадение побеждает
    for (var rule : props.getRules()) {
      if (rule.getPath() == null) continue;

      boolean pathOk = matcher.match(rule.getPath(), uri);
      if (!pathOk) continue;

      String ruleMethod = rule.getMethod() == null ? "ANY" : rule.getMethod().toUpperCase();
      boolean methodOk = ruleMethod.equals("ANY") || ruleMethod.equalsIgnoreCase(method);

      if (methodOk) return rule;
    }

    // Если нет правил - можно вернуть null и "не лимитировать", но лучше иметь default rule
    return null;
  }
}
