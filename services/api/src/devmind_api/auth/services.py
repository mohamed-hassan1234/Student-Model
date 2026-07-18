from datetime import timedelta
from typing import Any

from devmind_api.auth.models import (
    ROLE_PERMISSIONS,
    AuditEvent,
    AuthenticatedPrincipal,
    AuthSession,
    CreateUserInput,
    LoginAttempt,
    Permission,
    PublicUser,
    RefreshTokenFamily,
    RoleName,
    SecurityEvent,
    User,
    normalize_email,
    validate_password_strength,
)
from devmind_api.auth.repositories import AuthRepository
from devmind_api.auth.security import (
    AuthSecurityError,
    constant_time_equals,
    create_token,
    decode_token,
    hash_password,
    hash_token,
    new_secret_token,
    password_hash_needs_rehash,
    verify_password,
)
from devmind_api.config import Settings
from devmind_api.technology.hashing import stable_id
from devmind_shared.time import utc_now


class AuthServiceError(Exception):
    pass


class AuthService:
    def __init__(self, repository: AuthRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    async def create_user(
        self, data: CreateUserInput, actor: AuthenticatedPrincipal | None
    ) -> User:
        normalized = normalize_email(str(data.email))
        existing = await self._repository.get_user_by_email(normalized)
        if existing is not None:
            raise AuthServiceError("User already exists")
        now = utc_now()
        user = User(
            user_id=stable_id("usr", normalized),
            email=data.email,
            normalized_email=normalized,
            username=data.username,
            display_name=data.display_name,
            password_hash=hash_password(data.password),
            password_changed_at=now,
            created_at=now,
            updated_at=now,
        )
        created = await self._repository.create_user(user, data.roles)
        await self.audit(
            actor,
            action="users.create",
            resource_type="user",
            resource_id=created.user_id,
            result="success",
        )
        return created

    async def bootstrap_admin(self, email: str, username: str, password: str) -> User:
        validate_password_strength(password)
        users = await self._repository.list_users()
        for user in users:
            if RoleName.SUPER_ADMIN in await self._repository.get_user_roles(user.user_id):
                raise AuthServiceError("A super administrator already exists")
        return await self.create_user(
            CreateUserInput(
                email=email,
                username=username,
                display_name=username,
                roles=[RoleName.SUPER_ADMIN],
                **{"password": password},
            ),
            actor=None,
        )

    async def login(
        self,
        email: str,
        password: str,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        normalized = normalize_email(email)
        user = await self._repository.get_user_by_email(normalized)
        now = utc_now()
        success = False
        if user and user.active and (user.locked_until is None or user.locked_until <= now):
            success = verify_password(password, user.password_hash)
        await self._repository.record_login_attempt(
            LoginAttempt(
                attempt_id=stable_id("login", f"{normalized}:{now.isoformat()}"),
                normalized_email=normalized,
                success=success,
                ip_address=ip_address,
                created_at=now,
            )
        )
        if not user or not success:
            if user:
                count = user.failed_login_count + 1
                updates: dict[str, Any] = {"failed_login_count": count}
                if count >= self._settings.auth_failed_login_threshold:
                    updates["locked_until"] = now + timedelta(
                        minutes=self._settings.auth_lockout_minutes
                    )
                    await self.security_event(
                        "account_locked",
                        "medium",
                        actor_user_id=user.user_id,
                        reason="failed_login_threshold",
                    )
                await self._repository.update_user(user.user_id, updates)
            raise AuthServiceError("Invalid username or password")
        if not user.active:
            raise AuthServiceError("Invalid username or password")
        if password_hash_needs_rehash(user.password_hash):
            await self._repository.update_user(
                user.user_id, {"password_hash": hash_password(password)}
            )
        await self._repository.update_user(
            user.user_id,
            {"failed_login_count": 0, "locked_until": None, "last_login_at": now},
        )
        return await self._create_token_response(user, user_agent=user_agent, ip_address=ip_address)

    async def refresh(self, refresh_token: str) -> dict[str, Any]:
        payload = decode_token(self._settings, refresh_token, "refresh")
        refresh_hash = hash_token(refresh_token)
        session = await self._repository.get_session(str(payload["sid"]))
        if session is None or session.revoked:
            await self.security_event("revoked_refresh_used", "high", reason="session_revoked")
            raise AuthServiceError("Invalid refresh token")
        if session.expires_at <= utc_now():
            await self._repository.revoke_refresh_family(session.refresh_family_id)
            await self.security_event(
                "expired_refresh_used",
                "medium",
                actor_user_id=session.user_id,
                reason="session_expired",
            )
            raise AuthServiceError("Invalid refresh token")
        family = await self._repository.get_refresh_family(session.refresh_family_id)
        if family is None or family.revoked:
            await self._repository.update_session(session.session_id, {"revoked": True})
            await self.security_event(
                "revoked_refresh_family_used",
                "high",
                actor_user_id=session.user_id,
                reason="family_revoked",
            )
            raise AuthServiceError("Invalid refresh token")
        if not constant_time_equals(session.refresh_token_hash, refresh_hash):
            await self._repository.revoke_refresh_family(session.refresh_family_id)
            await self.security_event(
                "refresh_token_reuse_detected",
                "critical",
                actor_user_id=session.user_id,
                reason="refresh_token_hash_mismatch",
            )
            raise AuthServiceError("Invalid refresh token")
        user = await self._repository.get_user(session.user_id)
        if user is None or not user.active:
            await self._repository.update_session(session.session_id, {"revoked": True})
            raise AuthServiceError("Invalid refresh token")
        return await self._rotate_refresh_token(user, session)

    async def authenticate_access_token(self, access_token: str) -> AuthenticatedPrincipal:
        try:
            payload = decode_token(self._settings, access_token, "access")
        except AuthSecurityError as exc:
            raise AuthServiceError("Invalid access token") from exc
        user = await self._repository.get_user(str(payload["sub"]))
        session = await self._repository.get_session(str(payload["sid"]))
        if (
            user is None
            or session is None
            or session.revoked
            or session.expires_at <= utc_now()
            or not user.active
        ):
            raise AuthServiceError("Invalid access token")
        roles = await self._repository.get_user_roles(user.user_id)
        permissions = effective_permissions(roles)
        return AuthenticatedPrincipal(
            user=user,
            roles=roles,
            permissions=permissions,
            session_id=session.session_id,
            token_id=str(payload["jti"]),
        )

    async def logout(self, principal: AuthenticatedPrincipal) -> None:
        await self._repository.update_session(principal.session_id, {"revoked": True})
        await self.audit(principal, "auth.logout", "session", principal.session_id, "success")

    async def logout_all(self, principal: AuthenticatedPrincipal) -> None:
        await self._repository.revoke_user_sessions(principal.user.user_id)
        await self.audit(principal, "auth.logout_all", "user", principal.user.user_id, "success")

    async def change_password(
        self, principal: AuthenticatedPrincipal, current_password: str, new_password: str
    ) -> None:
        validate_password_strength(new_password)
        if not verify_password(current_password, principal.user.password_hash):
            raise AuthServiceError("Invalid current password")
        await self._repository.update_user(
            principal.user.user_id,
            {
                "password_hash": hash_password(new_password),
                "password_changed_at": utc_now(),
                "session_revocation_version": principal.user.session_revocation_version + 1,
            },
        )
        await self._repository.revoke_user_sessions(principal.user.user_id)
        await self.audit(
            principal, "auth.change_password", "user", principal.user.user_id, "success"
        )

    async def reset_password(
        self, actor: AuthenticatedPrincipal, user_id: str, new_password: str
    ) -> None:
        validate_password_strength(new_password)
        user = await self._repository.get_user(user_id)
        if user is None:
            raise AuthServiceError("User not found")
        await self._repository.update_user(
            user_id,
            {
                "password_hash": hash_password(new_password),
                "password_changed_at": utc_now(),
                "session_revocation_version": user.session_revocation_version + 1,
            },
        )
        await self._repository.revoke_user_sessions(user_id)
        await self.audit(actor, "users.reset_password", "user", user_id, "success")

    async def set_active(self, actor: AuthenticatedPrincipal, user_id: str, active: bool) -> User:
        user = await self._repository.update_user(user_id, {"active": active})
        if user is None:
            raise AuthServiceError("User not found")
        if not active:
            await self._repository.revoke_user_sessions(user_id)
        await self.audit(
            actor,
            "users.activate" if active else "users.deactivate",
            "user",
            user_id,
            "success",
        )
        return user

    async def public_user(self, user: User) -> PublicUser:
        roles = await self._repository.get_user_roles(user.user_id)
        permissions = sorted(effective_permissions(roles), key=lambda item: item.value)
        return PublicUser(
            user_id=user.user_id,
            email=user.email,
            username=user.username,
            display_name=user.display_name,
            active=user.active,
            roles=roles,
            permissions=permissions,
        )

    async def list_public_users(self, actor: AuthenticatedPrincipal) -> list[PublicUser]:
        users = await self._repository.list_users()
        await self.audit(actor, "users.read", "user", result="success")
        return [await self.public_user(user) for user in users]

    async def assign_role(
        self, actor: AuthenticatedPrincipal, user_id: str, role: RoleName
    ) -> PublicUser:
        user = await self._repository.get_user(user_id)
        if user is None:
            raise AuthServiceError("User not found")
        await self._repository.add_user_role(user_id, role)
        await self.audit(actor, "roles.assign", "user", user_id, "success", reason=role.value)
        refreshed = await self._repository.get_user(user_id)
        if refreshed is None:
            raise AuthServiceError("User not found")
        return await self.public_user(refreshed)

    async def remove_role(
        self, actor: AuthenticatedPrincipal, user_id: str, role: RoleName
    ) -> PublicUser:
        user = await self._repository.get_user(user_id)
        if user is None:
            raise AuthServiceError("User not found")
        roles = await self._repository.get_user_roles(user_id)
        if role in roles and len(roles) == 1:
            raise AuthServiceError("A user must retain at least one active role")
        if (
            role == RoleName.SUPER_ADMIN
            and RoleName.SUPER_ADMIN in roles
            and await self._repository.count_users_with_role(RoleName.SUPER_ADMIN) <= 1
        ):
            raise AuthServiceError("At least one super administrator must remain")
        await self._repository.remove_user_role(user_id, role)
        await self.audit(actor, "roles.remove", "user", user_id, "success", reason=role.value)
        refreshed = await self._repository.get_user(user_id)
        if refreshed is None:
            raise AuthServiceError("User not found")
        return await self.public_user(refreshed)

    async def revoke_sessions(self, actor: AuthenticatedPrincipal, user_id: str) -> None:
        user = await self._repository.get_user(user_id)
        if user is None:
            raise AuthServiceError("User not found")
        await self._repository.revoke_user_sessions(user_id)
        await self.audit(actor, "sessions.revoke", "user", user_id, "success")

    async def _create_token_response(
        self, user: User, *, user_agent: str | None, ip_address: str | None
    ) -> dict[str, Any]:
        now = utc_now()
        session_id = stable_id("sess", f"{user.user_id}:{now.isoformat()}")
        family_id = stable_id("rtf", f"{session_id}:{new_secret_token()}")
        refresh_token_id = stable_id("rt", new_secret_token())
        refresh_token = create_token(
            settings=self._settings,
            subject=user.user_id,
            session_id=session_id,
            token_id=refresh_token_id,
            token_type="refresh",  # noqa: S106 - JWT type label, not a secret.
            expires_delta=timedelta(minutes=self._settings.auth_refresh_token_minutes),
        )
        session = AuthSession(
            session_id=session_id,
            user_id=user.user_id,
            refresh_family_id=family_id,
            refresh_token_hash=hash_token(refresh_token),
            refresh_token_id=refresh_token_id,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=now + timedelta(minutes=self._settings.auth_refresh_token_minutes),
            created_at=now,
            updated_at=now,
        )
        family = RefreshTokenFamily(
            family_id=family_id,
            user_id=user.user_id,
            created_at=now,
            updated_at=now,
        )
        await self._repository.create_session(session, family)
        access_token_id = stable_id("at", new_secret_token())
        return {
            "access_token": create_token(
                settings=self._settings,
                subject=user.user_id,
                session_id=session_id,
                token_id=access_token_id,
                token_type="access",  # noqa: S106 - JWT type label, not a secret.
                expires_delta=timedelta(minutes=self._settings.auth_access_token_minutes),
            ),
            "refresh_token": refresh_token,
            "expires_in": self._settings.auth_access_token_minutes * 60,
            "csrf_token": new_secret_token(),
            "session_id": session_id,
        }

    async def _rotate_refresh_token(self, user: User, session: AuthSession) -> dict[str, Any]:
        refresh_token_id = stable_id("rt", new_secret_token())
        refresh_token = create_token(
            settings=self._settings,
            subject=user.user_id,
            session_id=session.session_id,
            token_id=refresh_token_id,
            token_type="refresh",  # noqa: S106 - JWT type label, not a secret.
            expires_delta=timedelta(minutes=self._settings.auth_refresh_token_minutes),
        )
        await self._repository.update_session(
            session.session_id,
            {
                "refresh_token_hash": hash_token(refresh_token),
                "refresh_token_id": refresh_token_id,
            },
        )
        access_token_id = stable_id("at", new_secret_token())
        return {
            "access_token": create_token(
                settings=self._settings,
                subject=user.user_id,
                session_id=session.session_id,
                token_id=access_token_id,
                token_type="access",  # noqa: S106 - JWT type label, not a secret.
                expires_delta=timedelta(minutes=self._settings.auth_access_token_minutes),
            ),
            "refresh_token": refresh_token,
            "expires_in": self._settings.auth_access_token_minutes * 60,
            "csrf_token": new_secret_token(),
            "session_id": session.session_id,
        }

    async def audit(
        self,
        actor: AuthenticatedPrincipal | None,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        result: str = "success",
        reason: str | None = None,
        risk_level: str = "low",
    ) -> None:
        await self._repository.record_audit_event(
            AuditEvent(
                event_id=stable_id("audit", f"{action}:{resource_id}:{utc_now().isoformat()}"),
                actor_user_id=actor.user.user_id if actor else None,
                actor_session_id=actor.session_id if actor else None,
                actor_roles=[role.value for role in actor.roles] if actor else [],
                actor_permissions=[perm.value for perm in actor.permissions] if actor else [],
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                result=result,
                reason=reason,
                risk_level=risk_level,
                created_at=utc_now(),
            )
        )

    async def security_event(
        self,
        event_type: str,
        severity: str,
        *,
        actor_user_id: str | None = None,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        await self._repository.record_security_event(
            SecurityEvent(
                event_id=stable_id("secevt", f"{event_type}:{utc_now().isoformat()}"),
                event_type=event_type,
                severity=severity,
                actor_user_id=actor_user_id,
                reason=reason,
                metadata=metadata or {},
                created_at=utc_now(),
            )
        )


def effective_permissions(roles: list[RoleName]) -> set[Permission]:
    permissions: set[Permission] = set()
    for role in roles:
        permissions.update(ROLE_PERMISSIONS.get(role, set()))
    return permissions
