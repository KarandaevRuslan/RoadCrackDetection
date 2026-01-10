package com.karandaev.roadCrackDetectionServer.security;

import org.springframework.security.authentication.AbstractAuthenticationToken;
import org.springframework.security.core.GrantedAuthority;

import java.util.Collection;

public class FirebaseAuthenticationToken extends AbstractAuthenticationToken {

  private final Object principal;
  private final String credentials; // исходный ID token

  // Неаутентифицированный (до проверки)
  public FirebaseAuthenticationToken(String idToken) {
    super(null);
    this.principal = null;
    this.credentials = idToken;
    setAuthenticated(false);
  }

  // Аутентифицированный (после проверки)
  public FirebaseAuthenticationToken(
      FirebasePrincipal principal, Collection<? extends GrantedAuthority> authorities) {
    super(authorities);
    this.principal = principal;
    this.credentials = null;
    setAuthenticated(true);
  }

  @Override
  public Object getCredentials() {
    return credentials;
  }

  @Override
  public Object getPrincipal() {
    return principal;
  }
}
