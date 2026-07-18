from collections.abc import Mapping
from typing import Any

from devmind_api.db import MongoDatabase
from devmind_api.governance.models import (
    ApprovalDecision,
    ApprovalRequest,
    GovernancePolicy,
    ProductionModelAssignment,
    StagingEvent,
    StagingRequest,
    governance_document,
)
from devmind_shared.time import utc_now


class GovernanceRepository:
    def __init__(self, database: MongoDatabase) -> None:
        self._database = database

    async def save_policy(self, policy: GovernancePolicy) -> GovernancePolicy:
        document = governance_document(policy)
        document["_id"] = policy.policy_id
        await self._database["governance_policies"].update_one(
            {"_id": policy.policy_id}, {"$set": document}, upsert=True
        )
        return policy

    async def list_policies(self) -> list[GovernancePolicy]:
        cursor = self._database["governance_policies"].find({}).sort("created_at", -1).limit(100)
        documents = await cursor.to_list(length=100)
        return [GovernancePolicy.model_validate(document) for document in documents]

    async def create_approval_request(self, request: ApprovalRequest) -> ApprovalRequest:
        document = governance_document(request)
        document["_id"] = request.approval_request_id
        await self._database["approval_requests"].insert_one(document)
        return request

    async def get_approval_request(self, approval_request_id: str) -> ApprovalRequest | None:
        document = await self._database["approval_requests"].find_one({"_id": approval_request_id})
        return ApprovalRequest.model_validate(document) if document else None

    async def list_approval_requests(self) -> list[ApprovalRequest]:
        cursor = self._database["approval_requests"].find({}).sort("created_at", -1).limit(200)
        documents = await cursor.to_list(length=200)
        return [ApprovalRequest.model_validate(document) for document in documents]

    async def update_approval_request(
        self, approval_request_id: str, updates: Mapping[str, Any]
    ) -> ApprovalRequest | None:
        payload = dict(updates)
        payload["updated_at"] = utc_now()
        await self._database["approval_requests"].update_one(
            {"_id": approval_request_id}, {"$set": payload}
        )
        return await self.get_approval_request(approval_request_id)

    async def record_decision(self, decision: ApprovalDecision) -> ApprovalDecision:
        document = governance_document(decision)
        document["_id"] = decision.decision_id
        await self._database["approval_decisions"].insert_one(document)
        return decision

    async def list_decisions(self, approval_request_id: str) -> list[ApprovalDecision]:
        cursor = (
            self._database["approval_decisions"]
            .find({"approval_request_id": approval_request_id})
            .sort("created_at", 1)
            .limit(100)
        )
        documents = await cursor.to_list(length=100)
        return [ApprovalDecision.model_validate(document) for document in documents]

    async def create_staging_request(self, request: StagingRequest) -> StagingRequest:
        document = governance_document(request)
        document["_id"] = request.staging_request_id
        await self._database["staging_requests"].insert_one(document)
        return request

    async def get_staging_request(self, staging_request_id: str) -> StagingRequest | None:
        document = await self._database["staging_requests"].find_one({"_id": staging_request_id})
        return StagingRequest.model_validate(document) if document else None

    async def list_staging_requests(self) -> list[StagingRequest]:
        cursor = self._database["staging_requests"].find({}).sort("created_at", -1).limit(200)
        documents = await cursor.to_list(length=200)
        return [StagingRequest.model_validate(document) for document in documents]

    async def update_staging_request(
        self, staging_request_id: str, updates: Mapping[str, Any]
    ) -> StagingRequest | None:
        payload = dict(updates)
        payload["updated_at"] = utc_now()
        await self._database["staging_requests"].update_one(
            {"_id": staging_request_id}, {"$set": payload}
        )
        return await self.get_staging_request(staging_request_id)

    async def record_staging_event(self, event: StagingEvent) -> StagingEvent:
        document = governance_document(event)
        document["_id"] = event.event_id
        await self._database["staging_events"].insert_one(document)
        return event

    async def record_assignment(
        self, assignment: ProductionModelAssignment
    ) -> ProductionModelAssignment:
        document = governance_document(assignment)
        document["_id"] = assignment.assignment_id
        await self._database["production_model_assignments"].insert_one(document)
        return assignment

    async def record_audit_event(self, event: dict[str, Any]) -> None:
        document = dict(event)
        document["_id"] = document["event_id"]
        await self._database["system_audit_events"].insert_one(document)

    async def record_security_event(self, event: dict[str, Any]) -> None:
        document = dict(event)
        document["_id"] = document["event_id"]
        await self._database["security_events"].insert_one(document)
