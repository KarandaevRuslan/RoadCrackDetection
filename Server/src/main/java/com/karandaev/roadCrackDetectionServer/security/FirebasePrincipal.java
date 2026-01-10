package com.karandaev.roadCrackDetectionServer.security;

import java.util.Set;

public record FirebasePrincipal(
    String uid, // uid: уникальный идентификатор пользователя в Firebase
    String email, // email: почта (может быть null, если анонимная авторизация)
    boolean emailVerified, // emailVerified: подтверждена ли почта
    Set<String> roles // roles: роли/права (если вы будете их выдавать)
    ) {}
