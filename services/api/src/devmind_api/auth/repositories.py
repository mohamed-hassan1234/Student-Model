from collections.abc import Mapping
from typing import Any

from devmind_api.auth.models import (
    AuditEvent,
    AuthSession,
    LoginAttempt,
    RefreshTokenFamily,
    RoleName,
    SecurityEvent,
    User,
)
from devmind_api.db import MongoDatabase
from devmind_api.technology.hashing import stable_id
from devmind_shared.time import utc_now


class AuthRepository:
    def __init__(self, database: MongoDatabase) -> None:
        self._database = database

    async def create_user(self, user: User, roles: list[RoleName]) -> User:
        document = user.model_dump(mode="python")
        document["_id"] = user.user_id
        await self._database["users"].insert_one(document)
        for role in roles:
            await self._database["user_roles"].insert_one(
                {
                    "_id": stable_id("urole", f"{user.user_id}:{role.value}"),
                    "user_id": user.user_id,
                    "role": role.value,
                    "removed": False,
                    "created_at": utc_now(),
                }
            )
        return user

    async def get_user_by_email(self, normalized_email: str) -> User | None:
        document = await self._database["users"].find_one({"normalized_email": normalized_email})
        return User.model_validate(document) if document else None

    async def get_user(self, user_id: str) -> User | None:
        document = await self._database["users"].find_one({"_id": user_id})
        return User.model_validate(document) if document else None

    async def list_users(self) -> list[User]:
        cursor = self._database["users"].find({}).sort("created_at", -1).limit(500)
        documents = await cursor.to_list(length=500)
        return [User.model_validate(document) for document in documents]

    async def update_user(self, user_id: str, updates: Mapping[str, Any]) -> User | None:
        payload = dict(updates)
        payload["updated_at"] = utc_now()
        await self._database["users"].update_one({"_id": user_id}, {"$set": payload})
        return await self.get_user(user_id)

    async def get_user_roles(self, user_id: str) -> list[RoleName]:
        cursor = self._database["user_roles"].find({"user_id": user_id, "removed": False}).limit(50)
        documents = await cursor.to_list(length=50)
        return [RoleName(str(document["role"])) for document in documents]

    async def add_user_role(self, user_id: str, role: RoleName) -> None:
        await self._database["user_roles"].update_one(
            {"_id": stable_id("urole", f"{user_id}:{role.value}")},
            {
                "$set": {
                    "_id": stable_id("urole", f"{user_id}:{role.value}"),
                    "user_id": user_id,
                    "role": role.value,
                    "removed": False,
                    "created_at": utc_now(),
                }
            },
            upsert=True,
        )

    async def remove_user_role(self, user_id: str, role: RoleName) -> None:
        await self._database["user_roles"].update_one(
            {"_id": stable_id("urole", f"{user_id}:{role.value}")},
            {"$set": {"removed": True, "updated_at": utc_now()}},
        )

    async def count_users_with_role(self, role: RoleName) -> int:
        cursor = self._database["user_roles"].find({"role": role.value, "removed": False})
        documents = await cursor.to_list(length=5000)
        return len(documents)

    async def create_session(self, session: AuthSession, family: RefreshTokenFamily) -> AuthSession:
        family_doc = family.model_dump(mode="python")
        family_doc["_id"] = family.family_id
        await self._database["refresh_token_families"].insert_one(family_doc)
        document = session.model_dump(mode="python")
        document["_id"] = session.session_id
        await self._database["auth_sessions"].insert_one(document)
        return session

    async def get_session(self, session_id: str) -> AuthSession | None:
        document = await self._database["auth_sessions"].find_one({"_id": session_id})
        return AuthSession.model_validate(document) if document else None

    async def get_refresh_family(self, family_id: str) -> RefreshTokenFamily | None:
        document = await self._database["refresh_token_families"].find_one({"_id": family_id})
        return RefreshTokenFamily.model_validate(document) if document else None

    async def get_session_by_refresh_hash(self, refresh_hash: str) -> AuthSession | None:
        document = await self._database["auth_sessions"].find_one(
            {"refresh_token_hash": refresh_hash}
        )
        return AuthSession.model_validate(document) if document else None

    async def update_session(
        self, session_id: str, updates: Mapping[str, Any]
    ) -> AuthSession | None:
        payload = dict(updates)
        payload["updated_at"] = utc_now()
        await self._database["auth_sessions"].update_one({"_id": session_id}, {"$set": payload})
        return await self.get_session(session_id)

    async def revoke_refresh_family(self, family_id: str) -> None:
        await self._database["refresh_token_families"].update_one(
            {"_id": family_id}, {"$set": {"revoked": True, "updated_at": utc_now()}}
        )
        sessions = (
            await self._database["auth_sessions"]
            .find({"refresh_family_id": family_id})
            .to_list(length=1000)
        )
        for session in sessions:
            await self.update_session(str(session["_id"]), {"revoked": True})

    async def revoke_user_sessions(self, user_id: str) -> None:
        sessions = (
            await self._database["auth_sessions"].find({"user_id": user_id}).to_list(length=1000)
        )
        for session in sessions:
            await self.update_session(str(session["_id"]), {"revoked": True})
            family_id = session.get("refresh_family_id")
            if family_id:
                await self.revoke_refresh_family(str(family_id))

    async def list_user_sessions(self, user_id: str) -> list[AuthSession]:
        cursor = self._database["auth_sessions"].find({"user_id": user_id}).limit(500)
        documents = await cursor.to_list(length=500)
        return [AuthSession.model_validate(document) for document in documents]

    async def record_login_attempt(self, attempt: LoginAttempt) -> None:
        document = attempt.model_dump(mode="python")
        document["_id"] = attempt.attempt_id
        await self._database["login_attempts"].insert_one(document)

    async def record_security_event(self, event: SecurityEvent) -> None:
        document = event.model_dump(mode="python")
        document["_id"] = event.event_id
        await self._database["security_events"].insert_one(document)

    async def record_audit_event(self, event: AuditEvent) -> None:
        document = event.model_dump(mode="python")
        document["_id"] = event.event_id
        await self._database["system_audit_events"].insert_one(document)
