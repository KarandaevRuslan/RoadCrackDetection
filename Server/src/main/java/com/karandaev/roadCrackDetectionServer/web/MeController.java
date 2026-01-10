package com.karandaev.roadCrackDetectionServer.web;

import com.karandaev.roadCrackDetectionServer.security.FirebasePrincipal;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
public class MeController {

  @GetMapping("/v1/me")
  public Map<String, Object> me(Authentication authentication) {
    // Authentication: объект Spring Security, который положили в SecurityContext
    Object principal = authentication.getPrincipal();

    if (principal instanceof FirebasePrincipal fp) {
      return Map.of(
          "uid", fp.uid(),
          "email", fp.email(),
          "emailVerified", fp.emailVerified(),
          "roles", fp.roles());
    }

    return Map.of("principal", principal);
  }
}
