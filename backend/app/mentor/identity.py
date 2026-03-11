from dataclasses import dataclass
from typing import Optional
from app.llm import llm_router, TaskType
from app.core.database import async_session
from sqlalchemy import select


@dataclass
class IdentitySchema:
    ideal_self: str
    description: str
    why: str
    role_models: list[str]
    target_timeline: str
    attributes: list[str]


IDENTITY_BUILDING_PROMPT = """You're helping a user define their ideal self - the person they want to become.

User's input: {input}

Extract the following in a structured way:
1. ideal_self: The role/identity (CEO, musician, entrepreneur, doctor, etc.)
2. description: How they describe this version of themselves
3. why: Why this matters to them (the deeper motivation)
4. role_models: People they admire who represent this (if mentioned)
5. target_timeline: When they want to achieve this (if mentioned)
6. attributes: Key traits/skills of this ideal self

If information is missing, ask a follow-up question to gather it.

Respond in JSON format:
{{"ideal_self": "...", "description": "...", "why": "...", "role_models": [...], "target_timeline": "...", "attributes": [...], "follow_up_question": "..." or null}}"""


class IdentityBuilder:
    def __init__(self):
        self.llm = llm_router

    async def build_identity(self, user_id: str, initial_input: str) -> dict:
        response = await self.llm.generate(
            prompt=IDENTITY_BUILDING_PROMPT.format(input=initial_input),
            task_type=TaskType.GENERATION,
            user_id=user_id
        )

        try:
            import json
            identity_data = json.loads(response.content)
        except:
            identity_data = {
                "ideal_self": initial_input,
                "description": initial_input,
                "why": None,
                "role_models": [],
                "target_timeline": None,
                "attributes": [],
                "follow_up_question": "That's a great start. Why does becoming this person matter to you?"
            }

        # Save to database and return saved identity with follow_up_question
        saved = await self.save_identity(user_id, identity_data)
        if identity_data.get("follow_up_question"):
            saved["follow_up_question"] = identity_data["follow_up_question"]
        return saved

    async def get_identity(self, user_id: str) -> Optional[dict]:
        async with async_session() as db:
            from app.models.identity import Identity
            result = await db.execute(
                select(Identity).where(Identity.user_id == user_id)
            )
            identity = result.scalar_one_or_none()

            if not identity:
                return None

            return {
                "id": identity.id,
                "ideal_self": identity.ideal_self,
                "description": identity.description,
                "why": identity.why,
                "role_models": identity.role_models or [],
                "target_timeline": identity.target_timeline,
                "attributes": identity.attributes or [],
                "anti_goals": identity.anti_goals or [],
                "constraints": {
                    "weekly_hours_available": identity.weekly_hours_available,
                    "monthly_budget": identity.monthly_budget,
                    "health_limits": identity.health_limits,
                    "risk_tolerance": identity.risk_tolerance,
                },
                "created_at": identity.created_at.isoformat() if identity.created_at else None
            }

    async def save_identity(self, user_id: str, identity_data: dict) -> dict:
        async with async_session() as db:
            from app.models.identity import Identity
            import uuid

            result = await db.execute(
                select(Identity).where(Identity.user_id == user_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.ideal_self = identity_data.get("ideal_self", existing.ideal_self)
                existing.description = identity_data.get("description", existing.description)
                existing.why = identity_data.get("why", existing.why)
                existing.role_models = identity_data.get("role_models", existing.role_models)
                existing.target_timeline = identity_data.get("target_timeline", existing.target_timeline)
                existing.attributes = identity_data.get("attributes", existing.attributes)
                await db.commit()
                await db.refresh(existing)
                identity = existing
            else:
                identity = Identity(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    ideal_self=identity_data.get("ideal_self", ""),
                    description=identity_data.get("description", ""),
                    why=identity_data.get("why"),
                    role_models=identity_data.get("role_models", []),
                    target_timeline=identity_data.get("target_timeline"),
                    attributes=identity_data.get("attributes", [])
                )
                db.add(identity)
                await db.commit()
                await db.refresh(identity)

            return {
                "id": identity.id,
                "ideal_self": identity.ideal_self,
                "description": identity.description,
                "why": identity.why,
                "role_models": identity.role_models or [],
                "target_timeline": identity.target_timeline,
                "attributes": identity.attributes or []
            }

    async def refine_identity(self, user_id: str, additional_input: str) -> dict:
        current = await self.get_identity(user_id)
        if not current:
            return await self.build_identity(user_id, additional_input)

        prompt = f"""Current identity: {current}
Additional input from user: {additional_input}

Refine the identity based on this new information. Keep what's still valid, update what's changed.
Respond in JSON format with keys: ideal_self, description, why, role_models, target_timeline, attributes"""

        response = await self.llm.generate(prompt=prompt, task_type=TaskType.GENERATION, user_id=user_id)

        try:
            import json
            refined = json.loads(response.content)
            return await self.save_identity(user_id, refined)
        except:
            return current


identity_builder = IdentityBuilder()
