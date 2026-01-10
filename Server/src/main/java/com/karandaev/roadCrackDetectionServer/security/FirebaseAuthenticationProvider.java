package com.karandaev.roadCrackDetectionServer.security;

import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseToken;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Component;

import java.util.Set;
import java.util.stream.Collectors;

@Component
public class FirebaseAuthenticationProvider implements AuthenticationProvider {

  @Override
  public Authentication authenticate(Authentication authentication) {
    if (!(authentication instanceof FirebaseAuthenticationToken token)) {
      return null;
    }

    String idToken = (String) token.getCredentials();
    if (idToken == null || idToken.isBlank()) {
      throw new BadCredentialsException("Missing Firebase ID token");
    }

    try {
      // verifyIdToken: проверка подписи, срока действия, issuer, audience (внутренняя логика SDK)
      FirebaseToken decoded = FirebaseAuth.getInstance().verifyIdToken(idToken);

      // customClaims: пользовательские claims (поля) - удобно для ролей
      // Пример: {"roles": ["USER","ADMIN"]}
      Object rolesObj = decoded.getClaims().get("roles");
      Set<String> roles = ClaimUtils.extractRoles(rolesObj);

      var authorities =
          roles.stream()
              .map(r -> "ROLE_" + r) // Spring convention: роли начинаются с ROLE_
              .map(SimpleGrantedAuthority::new)
              .collect(Collectors.toSet());

      FirebasePrincipal principal =
          new FirebasePrincipal(
              decoded.getUid(),
              decoded.getEmail(),
              Boolean.TRUE.equals(decoded.isEmailVerified()),
              roles);

      return new FirebaseAuthenticationToken(principal, authorities);
    } catch (Exception e) {
      // BadCredentialsException: стандартная ошибка Spring для "неверных" учетных данных
      throw new BadCredentialsException("Invalid Firebase ID token", e);
    }
  }

  @Override
  public boolean supports(Class<?> authentication) {
    return FirebaseAuthenticationToken.class.isAssignableFrom(authentication);
  }

  // Вспомогательный класс для вытаскивания ролей из claims
  static class ClaimUtils {
    static Set<String> extractRoles(Object rolesObj) {
      if (rolesObj == null) return Set.of("USER"); // дефолтная роль
      if (rolesObj instanceof Iterable<?> it) {
        Set<String> out = new java.util.HashSet<>();
        for (Object o : it) {
          if (o != null) out.add(o.toString());
        }
        return out.isEmpty() ? Set.of("USER") : out;
      }
      // если пришло строкой, например "ADMIN"
      return Set.of(rolesObj.toString());
    }
  }
}
