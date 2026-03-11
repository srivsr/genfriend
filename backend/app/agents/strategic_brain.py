import json
import logging
from datetime import datetime, date, timedelta
from .base import BaseAgent, AgentContext, AgentResponse
from app.llm import TaskType
from app.core.database import async_session
from app.repositories.strategic_brain_repository import (
    OpportunityScoreRepository, DecisionLogRepository,
    ExperimentRepository, DistractionRuleRepository
)
from app.repositories.goal_repository import GoalRepository
from sqlalchemy import select
from app.models.identity import Identity

logger = logging.getLogger(__name__)


class StrategicBrainAgent(BaseAgent):
    name = "strategic_brain"
    description = "Evaluates opportunities, logs decisions, manages experiments and distraction rules"

    async def process(self, message: str, context: AgentContext) -> AgentResponse:
        lower = message.lower()
        if any(w in lower for w in ["score", "evaluate idea", "opportunity", "should i pursue"]):
            return await self.score_opportunity(context.user_id, message)
        if any(w in lower for w in ["decision log", "i decided", "log decision"]):
            return await self.log_decision(context.user_id, message)
        if any(w in lower for w in ["experiment", "hypothesis", "test this"]):
            return await self.handle_experiment(context.user_id, message)
        if any(w in lower for w in ["distraction rule", "focus rule", "block rule"]):
            return await self.manage_rules(context.user_id, message)
        if "strategic overview" in lower:
            return await self.strategic_overview(context.user_id)
        return await self.score_opportunity(context.user_id, message)

    async def score_opportunity(self, user_id: str, description: str) -> AgentResponse:
        async with async_session() as db:
            identity = await self._get_identity(user_id, db)
            anti_goals = await self._get_anti_goals(user_id, db)
            constraints = await self._get_constraints(user_id, db)
            rules = await self._get_active_rules(user_id, db)
            goals_repo = GoalRepository(db)
            active_goals = await goals_repo.get_active(user_id)
            goals_context = "\n".join([f"- {g.title} ({g.progress_percent}%)" for g in active_goals[:5]])

        ideal_self = identity.ideal_self if identity and hasattr(identity, 'ideal_self') and identity.ideal_self else "your best self"

        anti_goals_text = "\n".join([f"- {ag}" for ag in anti_goals]) if anti_goals else "None defined"
        rules_text = "\n".join([f"- {r.rule_name}: IF {r.condition} THEN {r.action}" for r in rules]) if rules else "None"

        constraints_parts = []
        if constraints.get("weekly_hours_available") is not None:
            constraints_parts.append(f"- Available hours/week: {constraints['weekly_hours_available']}")
        if constraints.get("monthly_budget") is not None:
            constraints_parts.append(f"- Monthly budget: ${constraints['monthly_budget']}")
        if constraints.get("health_limits"):
            constraints_parts.append(f"- Health limits: {constraints['health_limits']}")
        if constraints.get("risk_tolerance"):
            constraints_parts.append(f"- Risk tolerance: {constraints['risk_tolerance']}")
        constraints_text = "\n".join(constraints_parts) if constraints_parts else "None defined"

        prompt = f"""Score this opportunity/idea on 6 dimensions (0-10 each).

Opportunity: {description}

User's active goals:
{goals_context}

User's constraints:
{constraints_text}

User's anti-goals (things they want to AVOID):
{anti_goals_text}

User's distraction rules:
{rules_text}

Score each dimension 0-10:
1. revenue_potential - How much income/value could this generate?
2. strategic_fit - How well does this align with current goals?
3. effort_complexity - How easy is this to execute given the user's constraints (available hours, budget, health limits)? (10=easy, 0=very hard). If the opportunity requires more hours than available or exceeds budget, score LOW.
4. skill_match - How well do current skills match what's needed?
5. time_to_first_win - How quickly can they see results? (10=fast, 0=slow)
6. risk_regret_cost - How low is the risk/regret? Factor in the user's risk tolerance — if tolerance is "low", penalize risky opportunities harder. (10=low risk, 0=high risk)

Also check for anti-goal conflicts and distraction rule violations.

Respond in JSON:
{{
  "title": "short title for this opportunity",
  "revenue_potential": 0,
  "strategic_fit": 0,
  "effort_complexity": 0,
  "skill_match": 0,
  "time_to_first_win": 0,
  "risk_regret_cost": 0,
  "reasoning": {{"summary": "...", "strengths": ["..."], "risks": ["..."]}},
  "anti_goal_conflicts": ["list of conflicts or empty"],
  "constraint_warnings": ["list of constraint issues or empty"],
  "verdict": "pursue / pass / revisit later"
}}"""

        response = await self._generate(prompt, task_type=TaskType.COMPLEX_REASONING)

        try:
            data = json.loads(response.strip().removeprefix("```json").removesuffix("```").strip())
        except json.JSONDecodeError:
            return AgentResponse(content=response, metadata={"parse_error": True})

        scores = [data.get(k, 0) for k in [
            "revenue_potential", "strategic_fit", "effort_complexity",
            "skill_match", "time_to_first_win", "risk_regret_cost"
        ]]
        total = sum(scores) / 6.0

        async with async_session() as db:
            repo = OpportunityScoreRepository(db)
            opp = await repo.create(
                user_id=user_id,
                title=data.get("title", "Untitled"),
                description=description,
                revenue_potential=data.get("revenue_potential", 0),
                strategic_fit=data.get("strategic_fit", 0),
                effort_complexity=data.get("effort_complexity", 0),
                skill_match=data.get("skill_match", 0),
                time_to_first_win=data.get("time_to_first_win", 0),
                risk_regret_cost=data.get("risk_regret_cost", 0),
                total_score=round(total, 1),
                reasoning=data.get("reasoning"),
                anti_goal_conflicts=data.get("anti_goal_conflicts"),
                status="evaluated"
            )

        conflicts = data.get("anti_goal_conflicts", [])
        constraint_warnings = data.get("constraint_warnings", [])
        verdict = data.get("verdict", "revisit later")
        reasoning_summary = data.get("reasoning", {}).get("summary", "")

        twin_prompt = f"""You are the user's Future Self — the version of them who already became {ideal_self}.
You just evaluated an opportunity they're considering. Speak as someone who's been there.

Opportunity: {description}
Your verdict: {verdict}
Score: {round(total, 1)}/10
Key reasoning: {reasoning_summary}
Anti-goal conflicts: {conflicts if conflicts else 'None'}
Constraint warnings: {constraint_warnings if constraint_warnings else 'None'}

Write a brief response (3-5 sentences) as Future You:
- If it's a good fit: encourage with specifics about why this aligns with the path
- If it's a bad fit: explain from experience why you'd skip this, without criticizing the idea itself
- Reference their constraints or anti-goals naturally, like someone who lived through the same trade-offs
- End with a clear recommendation: pursue, pass, or revisit later

Do NOT use score numbers or dimension names. Speak naturally, like a mentor who already made it."""

        twin_voice = await self._generate(twin_prompt, task_type=TaskType.GENERATION)

        scorecard = (
            f"\n\n---\n*Score: {round(total, 1)}/10 — "
            f"Revenue {data.get('revenue_potential')} | Fit {data.get('strategic_fit')} | "
            f"Effort {data.get('effort_complexity')} | Skills {data.get('skill_match')} | "
            f"Speed {data.get('time_to_first_win')} | Risk {data.get('risk_regret_cost')}*"
        )

        return AgentResponse(
            content=twin_voice + scorecard,
            data={"opportunity_id": opp.id, "scores": data}
        )

    async def log_decision(self, user_id: str, message: str) -> AgentResponse:
        prompt = f"""Extract a structured decision from this message.

Message: {message}

Respond in JSON:
{{
  "decision": "what was decided",
  "why": "reasoning behind it",
  "expected_outcome": "what they expect to happen",
  "review_days": 14,
  "tags": ["tag1", "tag2"]
}}"""
        response = await self._generate(prompt, task_type=TaskType.GENERATION)

        try:
            data = json.loads(response.strip().removeprefix("```json").removesuffix("```").strip())
        except json.JSONDecodeError:
            return AgentResponse(content="I couldn't parse that decision. Could you rephrase?")

        review_days = data.get("review_days", 14)
        review_date = date.today() + timedelta(days=review_days)

        async with async_session() as db:
            repo = DecisionLogRepository(db)
            entry = await repo.create(
                user_id=user_id,
                decision=data.get("decision", message),
                why=data.get("why"),
                expected_outcome=data.get("expected_outcome"),
                review_date=review_date,
                tags=data.get("tags"),
                status="pending_review"
            )

        return AgentResponse(
            content=(
                f"Decision logged: **{data.get('decision')}**\n\n"
                f"Why: {data.get('why')}\n"
                f"Expected: {data.get('expected_outcome')}\n"
                f"Review date: {review_date.isoformat()}"
            ),
            data={"decision_id": entry.id}
        )

    async def handle_experiment(self, user_id: str, message: str) -> AgentResponse:
        lower = message.lower()
        if any(w in lower for w in ["close", "result", "learned", "finding"]):
            return await self._close_experiment(user_id, message)
        return await self._open_experiment(user_id, message)

    async def _open_experiment(self, user_id: str, message: str) -> AgentResponse:
        prompt = f"""Extract a structured experiment from this message.

Message: {message}

Respond in JSON:
{{
  "hypothesis": "if X then Y",
  "action": "what to do to test this",
  "tags": ["tag1"]
}}"""
        response = await self._generate(prompt, task_type=TaskType.GENERATION)

        try:
            data = json.loads(response.strip().removeprefix("```json").removesuffix("```").strip())
        except json.JSONDecodeError:
            return AgentResponse(content="Could you rephrase your experiment hypothesis?")

        async with async_session() as db:
            repo = ExperimentRepository(db)
            exp = await repo.create(
                user_id=user_id,
                hypothesis=data.get("hypothesis", message),
                action=data.get("action"),
                tags=data.get("tags"),
                status="open"
            )

        return AgentResponse(
            content=(
                f"Experiment opened: **{data.get('hypothesis')}**\n\n"
                f"Action: {data.get('action')}\n"
                f"Status: open"
            ),
            data={"experiment_id": exp.id}
        )

    async def _close_experiment(self, user_id: str, message: str) -> AgentResponse:
        async with async_session() as db:
            repo = ExperimentRepository(db)
            open_exps = await repo.get_open(user_id)
            if not open_exps:
                return AgentResponse(content="No open experiments to close.")

            exp = open_exps[0]
            prompt = f"""The user wants to close an experiment.

Experiment hypothesis: {exp.hypothesis}
Action: {exp.action}

User message: {message}

Extract result and learning in JSON:
{{
  "result": "what happened",
  "learning": "key takeaway"
}}"""
            response = await self._generate(prompt, task_type=TaskType.GENERATION)

            try:
                data = json.loads(response.strip().removeprefix("```json").removesuffix("```").strip())
            except json.JSONDecodeError:
                data = {"result": message, "learning": ""}

            await repo.update(
                exp.id,
                result=data.get("result", message),
                learning=data.get("learning"),
                status="closed",
                closed_at=datetime.utcnow()
            )

        return AgentResponse(
            content=(
                f"Experiment closed: **{exp.hypothesis}**\n\n"
                f"Result: {data.get('result')}\n"
                f"Learning: {data.get('learning')}"
            ),
            data={"experiment_id": exp.id}
        )

    async def manage_rules(self, user_id: str, message: str) -> AgentResponse:
        prompt = f"""The user wants to create or manage a distraction/focus rule.

Message: {message}

Extract in JSON:
{{
  "action": "create" or "list" or "toggle",
  "rule_name": "short name",
  "condition": "when this happens",
  "rule_action": "do this instead"
}}"""
        response = await self._generate(prompt, task_type=TaskType.GENERATION)

        try:
            data = json.loads(response.strip().removeprefix("```json").removesuffix("```").strip())
        except json.JSONDecodeError:
            return AgentResponse(content="Could you describe the rule more clearly?")

        action = data.get("action", "create")

        async with async_session() as db:
            repo = DistractionRuleRepository(db)

            if action == "list":
                rules = await repo.get_active_rules(user_id)
                if not rules:
                    return AgentResponse(content="No active distraction rules.")
                lines = [f"- **{r.rule_name}**: IF {r.condition} THEN {r.action}" for r in rules]
                return AgentResponse(content="**Active Rules:**\n" + "\n".join(lines))

            rule = await repo.create(
                user_id=user_id,
                rule_name=data.get("rule_name", "Custom Rule"),
                condition=data.get("condition", ""),
                action=data.get("rule_action", ""),
                rule_type="custom",
                is_active=True
            )

        return AgentResponse(
            content=f"Rule created: **{rule.rule_name}**\nIF {rule.condition} THEN {rule.action}",
            data={"rule_id": rule.id}
        )

    async def check_anti_goal_conflicts(self, user_id: str, proposal: str) -> list[str]:
        async with async_session() as db:
            anti_goals = await self._get_anti_goals(user_id, db)
        if not anti_goals:
            return []

        prompt = f"""Check if this proposal conflicts with any anti-goals.

Proposal: {proposal}

Anti-goals (things to AVOID):
{chr(10).join(f'- {ag}' for ag in anti_goals)}

List any conflicts. If none, respond with empty JSON array.
Respond as JSON array of strings: ["conflict 1", "conflict 2"] or []"""

        response = await self._generate(prompt, task_type=TaskType.CLASSIFICATION)
        try:
            return json.loads(response.strip().removeprefix("```json").removesuffix("```").strip())
        except json.JSONDecodeError:
            return []

    async def check_distraction_rules(self, user_id: str) -> list[dict]:
        async with async_session() as db:
            repo = DistractionRuleRepository(db)
            rules = await repo.get_active_rules(user_id)
            if not rules:
                return []

            goals_repo = GoalRepository(db)
            active_goals = await goals_repo.get_active(user_id)

        builtin_violations = []
        for rule in rules:
            if rule.rule_type == "builtin":
                if "goals under" in rule.condition.lower() and active_goals:
                    threshold = 50
                    low_goals = [g for g in active_goals if (g.progress_percent or 0) < threshold]
                    if low_goals:
                        builtin_violations.append({
                            "rule": rule.rule_name,
                            "violation": f"{len(low_goals)} goals under {threshold}% progress",
                            "action": rule.action
                        })
                continue

        if not any(r.rule_type == "custom" for r in rules):
            return builtin_violations

        custom_rules = [r for r in rules if r.rule_type == "custom"]
        goals_summary = "\n".join([f"- {g.title}: {g.progress_percent}%" for g in active_goals[:5]])
        rules_text = "\n".join([f"- {r.rule_name}: IF {r.condition} THEN {r.action}" for r in custom_rules])

        prompt = f"""Evaluate these distraction rules against current state.

Rules:
{rules_text}

Current goals:
{goals_summary}

For each rule, determine if it's being violated. Respond in JSON:
[{{"rule": "name", "violated": true/false, "violation": "description", "action": "suggested action"}}]"""

        response = await self._generate(prompt, task_type=TaskType.CLASSIFICATION)
        try:
            results = json.loads(response.strip().removeprefix("```json").removesuffix("```").strip())
            violations = [r for r in results if r.get("violated")]
            return builtin_violations + violations
        except json.JSONDecodeError:
            return builtin_violations

    async def review_decision(self, user_id: str, decision_id: str, actual_outcome: str) -> AgentResponse:
        async with async_session() as db:
            repo = DecisionLogRepository(db)
            decision = await repo.get_by_id(decision_id)
            if not decision or decision.user_id != user_id:
                return AgentResponse(content="Decision not found.")

            await repo.update(decision_id, actual_outcome=actual_outcome, status="reviewed")

        prompt = f"""Analyze this decision review and extract a learning.

Decision: {decision.decision}
Why: {decision.why}
Expected outcome: {decision.expected_outcome}
Actual outcome: {actual_outcome}

Respond in JSON:
{{
  "learning_summary": "concise summary of what was learned",
  "is_significant": true/false,
  "experiment_hypothesis": "if significant, a follow-up experiment hypothesis or null"
}}"""

        response = await self._generate(prompt, task_type=TaskType.COMPLEX_REASONING)
        try:
            data = json.loads(response.strip().removeprefix("```json").removesuffix("```").strip())
        except json.JSONDecodeError:
            data = {"learning_summary": actual_outcome, "is_significant": False}

        experiment_id = None
        if data.get("is_significant") and data.get("experiment_hypothesis"):
            async with async_session() as db:
                exp_repo = ExperimentRepository(db)
                exp = await exp_repo.create(
                    user_id=user_id,
                    hypothesis=data["experiment_hypothesis"],
                    action=f"Follow-up from decision review: {decision.decision}",
                    tags=["decision-review", "auto-generated"],
                    status="open"
                )
                experiment_id = exp.id

        return AgentResponse(
            content=(
                f"**Decision Reviewed:** {decision.decision}\n\n"
                f"**Actual outcome:** {actual_outcome}\n"
                f"**Learning:** {data.get('learning_summary', '')}"
                + (f"\n\n**New experiment opened:** {data.get('experiment_hypothesis')}" if experiment_id else "")
            ),
            data={
                "decision_id": decision_id,
                "learning_summary": data.get("learning_summary"),
                "is_significant": data.get("is_significant", False),
                "experiment_id": experiment_id,
            }
        )

    async def strategic_overview(self, user_id: str) -> AgentResponse:
        async with async_session() as db:
            opp_repo = OpportunityScoreRepository(db)
            dec_repo = DecisionLogRepository(db)
            exp_repo = ExperimentRepository(db)
            rule_repo = DistractionRuleRepository(db)

            opportunities = await opp_repo.get_by_user(user_id, limit=5)
            pending_reviews = await dec_repo.get_pending_reviews(user_id)
            open_experiments = await exp_repo.get_open(user_id)
            active_rules = await rule_repo.get_active_rules(user_id)
            anti_goals = await self._get_anti_goals(user_id, db)

        sections = []

        if opportunities:
            opp_lines = [f"- {o.title}: {o.total_score}/10 ({o.status})" for o in opportunities]
            sections.append("**Recent Opportunities:**\n" + "\n".join(opp_lines))

        if pending_reviews:
            dec_lines = [f"- {d.decision} (review by {d.review_date})" for d in pending_reviews]
            sections.append("**Decisions Due for Review:**\n" + "\n".join(dec_lines))

        if open_experiments:
            exp_lines = [f"- {e.hypothesis}" for e in open_experiments]
            sections.append("**Open Experiments:**\n" + "\n".join(exp_lines))

        if active_rules:
            rule_lines = [f"- {r.rule_name}" for r in active_rules]
            sections.append("**Active Focus Rules:**\n" + "\n".join(rule_lines))

        if anti_goals:
            sections.append("**Anti-Goals:**\n" + "\n".join(f"- {ag}" for ag in anti_goals))

        if not sections:
            return AgentResponse(content="No strategic data yet. Try scoring an opportunity or logging a decision!")

        prompt = f"""Provide a brief strategic overview based on this data:

{chr(10).join(sections)}

Give 2-3 actionable insights about their strategic position. Be concise."""

        analysis = await self._generate(prompt, task_type=TaskType.GENERATION)
        return AgentResponse(
            content="**Strategic Overview**\n\n" + "\n\n".join(sections) + "\n\n**Analysis:**\n" + analysis,
            data={"opportunities": len(opportunities), "pending_reviews": len(pending_reviews),
                  "open_experiments": len(open_experiments), "active_rules": len(active_rules)}
        )

    async def _get_identity(self, user_id: str, db) -> Identity | None:
        result = await db.execute(
            select(Identity).where(Identity.user_id == user_id, Identity.is_active == True)
        )
        return result.scalar_one_or_none()

    async def _get_anti_goals(self, user_id: str, db) -> list[str]:
        identity = await self._get_identity(user_id, db)
        if identity and identity.anti_goals:
            return identity.anti_goals if isinstance(identity.anti_goals, list) else []
        return []

    async def _get_constraints(self, user_id: str, db) -> dict:
        identity = await self._get_identity(user_id, db)
        if not identity:
            return {}
        return {
            "weekly_hours_available": identity.weekly_hours_available,
            "monthly_budget": identity.monthly_budget,
            "health_limits": identity.health_limits,
            "risk_tolerance": identity.risk_tolerance,
        }

    async def _get_active_rules(self, user_id: str, db) -> list:
        repo = DistractionRuleRepository(db)
        return await repo.get_active_rules(user_id)
