package com.karandaev.roadCrackDetectionServer.security;

import com.karandaev.roadCrackDetectionServer.ratelimit.RateLimitProperties;
import com.karandaev.roadCrackDetectionServer.ratelimit.RateLimiterService;
import com.karandaev.roadCrackDetectionServer.ratelimit.RateLimitingFilter;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.ProviderManager;
import org.springframework.security.authorization.AuthorizationDecision;
import org.springframework.security.config.Customizer;

import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;

import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@Configuration
@EnableConfigurationProperties(RateLimitProperties.class)
public class SecurityConfig {

  @Bean
  public AuthenticationManager authenticationManager(FirebaseAuthenticationProvider provider) {
    // ProviderManager: стандартный AuthenticationManager, который делегирует провайдерам
    return new ProviderManager(provider);
  }

  @Bean
  public RateLimiterService rateLimiterService(RateLimitProperties props) {
    return new RateLimiterService(props);
  }

  @Bean
  public RateLimitingFilter rateLimitingFilter(
      RateLimitProperties props, RateLimiterService service) {
    return new RateLimitingFilter(props, service);
  }

  @Bean
  public SecurityFilterChain securityFilterChain(
      HttpSecurity http,
      AuthenticationManager authenticationManager,
      RateLimitingFilter rateLimitingFilter)
      throws Exception {

    var firebaseFilter = new FirebaseAuthenticationFilter(authenticationManager);

    return http.csrf(AbstractHttpConfigurer::disable) // CSRF: защита браузерных форм;
        .sessionManagement(sm -> sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
        .authorizeHttpRequests(
            auth ->
                auth.requestMatchers("/public/**")
                    .permitAll()
                    // /v1/** доступен только если пользователь залогинен и почта подтверждена
                    .requestMatchers("/v1/**")
                    .access(
                        (authentication, context) -> {
                          var a = authentication.get();
                          var principal = a.getPrincipal();

                          if (principal instanceof FirebasePrincipal fp) {
                            return new AuthorizationDecision(fp.emailVerified());
                          }
                          return new AuthorizationDecision(false);
                        })
                    .anyRequest()
                    .denyAll())
        // 1) сначала Firebase auth
        .addFilterBefore(firebaseFilter, UsernamePasswordAuthenticationFilter.class)
        // 2) потом rate limiting (уже есть uid в SecurityContext)
        .addFilterAfter(rateLimitingFilter, FirebaseAuthenticationFilter.class)
        .httpBasic(Customizer.withDefaults())
        .build();
  }
}
