from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum

from app.llm.router import LLMRouter, TaskType


class ScoreStatus(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    OKAY = "okay"
    NEEDS_WORK = "needs_work"


@dataclass
class PrincipleScore:
    score: int  # 1-5
    max_score: int = 5
    status: ScoreStatus = ScoreStatus.OKAY
    feedback: str = ""
    improvement: Optional[str] = None


@dataclass
class LockeLathameValidation:
    clarity: PrincipleScore
    challenge: PrincipleScore
    commitment: PrincipleScore
    feedback: PrincipleScore
    complexity: PrincipleScore
    total_score: int
    max_score: int = 25
    percentage: float = 0.0
    overall_status: str = "needs_work"
    strengths: List[str] = None
    priority_improvement: Dict = None
    research_note: str = "Goals scoring 20+ on Locke-Latham criteria are 2-3x more likely to be achieved."


PRINCIPLE_DESCRIPTIONS = {
    "clarity": {
        "name": "Clarity",
        "description": "Is the goal specific and unambiguous?",
        "score_5": "Specific, measurable, time-bound, unambiguous. Example: 'Run a 5K in under 30 minutes by March 1'",
        "score_4": "Specific with minor ambiguity. Example: 'Get better at running, aiming for 5K distance'",
        "score_3": "Somewhat specific. Example: 'Improve my running'",
        "score_2": "Vague. Example: 'Get fit'",
        "score_1": "Extremely vague. Example: 'Be healthier'",
        "improvement_template": "Try adding a specific number or deadline: 'I want to [verb] [measurable outcome] by [date]'"
    },
    "challenge": {
        "name": "Challenge",
        "description": "Is it stretching but achievable? (70-90% confidence sweet spot)",
        "score_5": "Stretching but achievable — 70-90% confidence. Pushes growth without demoralizing",
        "score_4": "Challenging, might be slightly too easy or slightly ambitious",
        "score_3": "Either moderately easy or moderately hard",
        "score_2": "Too easy (no growth) or too hard (likely failure)",
        "score_1": "Trivial (no challenge) or impossible (certain failure)",
        "improvement_template": "On a scale of 1-10, how confident are you? Aim for 7-8. If below 5, make it smaller. If 9-10, stretch it."
    },
    "commitment": {
        "name": "Commitment",
        "description": "Is there emotional investment and personal meaning?",
        "score_5": "Strong emotional connection — vivid outcome, clear personal why, identity-connected",
        "score_4": "Clear motivation, some emotional connection",
        "score_3": "Moderate interest, logical reasons only",
        "score_2": "Weak connection, feels like a 'should' goal",
        "score_1": "No apparent investment, purely external pressure",
        "improvement_template": "Why does this matter to YOU specifically? How would achieving it change how you see yourself?"
    },
    "feedback": {
        "name": "Feedback",
        "description": "Are there clear progress indicators and check-in mechanisms?",
        "score_5": "Clear milestones, regular check-ins planned, progress is measurable",
        "score_4": "Some measurement system, periodic review planned",
        "score_3": "Basic tracking possible but not systematic",
        "score_2": "Vague sense of progress only",
        "score_1": "No way to know if progressing",
        "improvement_template": "How will you know you're making progress each week? Let's define milestones."
    },
    "complexity": {
        "name": "Complexity",
        "description": "Is the scope right-sized for the timeframe?",
        "score_5": "Right-sized — can be broken into clear tasks, appropriate scope for timeline",
        "score_4": "Mostly appropriate, minor adjustment might help",
        "score_3": "Might need some scope adjustment",
        "score_2": "Too big or too small for stated timeline",
        "score_1": "Wildly mismatched scope and timeline",
        "improvement_template": "This might be [too big/too small] for [timeframe]. Consider [adjusting scope/timeline]."
    }
}


class LockeLathameValidator:
    def __init__(self, llm: LLMRouter):
        self.llm = llm

    async def validate(
        self,
        goal_wish: str,
        goal_outcome: Optional[str] = None,
        goal_obstacle: Optional[str] = None,
        if_then_plan: Optional[Dict] = None,
        future_you: Optional[str] = None,
        timeframe: str = "3_months"
    ) -> LockeLathameValidation:
        prompt = self._build_validation_prompt(
            goal_wish, goal_outcome, goal_obstacle, if_then_plan, future_you, timeframe
        )
        response = await self.llm.generate(prompt, task_type=TaskType.ANALYSIS, max_tokens=1500)
        return self._parse_validation_response(response)

    def validate_sync(
        self,
        goal_wish: str,
        goal_outcome: Optional[str] = None,
        timeframe: str = "3_months",
        confidence_level: Optional[int] = None,
        has_milestones: bool = False,
        has_emotional_why: bool = False
    ) -> LockeLathameValidation:
        clarity = self._score_clarity(goal_wish, goal_outcome)
        challenge = self._score_challenge(confidence_level)
        commitment = self._score_commitment(has_emotional_why, goal_outcome)
        feedback = self._score_feedback(has_milestones)
        complexity = self._score_complexity(goal_wish, timeframe)

        scores = [clarity, challenge, commitment, feedback, complexity]
        total = sum(s.score for s in scores)
        percentage = (total / 25) * 100

        if total >= 20:
            overall = "strong"
        elif total >= 15:
            overall = "solid"
        else:
            overall = "needs_work"

        strengths = [
            PRINCIPLE_DESCRIPTIONS[name]["name"]
            for name, score in zip(["clarity", "challenge", "commitment", "feedback", "complexity"], scores)
            if score.score >= 4
        ]

        weakest = min(scores, key=lambda s: s.score)
        weakest_idx = scores.index(weakest)
        weakest_name = ["clarity", "challenge", "commitment", "feedback", "complexity"][weakest_idx]

        return LockeLathameValidation(
            clarity=clarity,
            challenge=challenge,
            commitment=commitment,
            feedback=feedback,
            complexity=complexity,
            total_score=total,
            percentage=percentage,
            overall_status=overall,
            strengths=strengths,
            priority_improvement={
                "principle": weakest_name,
                "suggestion": PRINCIPLE_DESCRIPTIONS[weakest_name]["improvement_template"],
                "impact": "Will help you stay motivated and catch issues early"
            }
        )

    def _score_clarity(self, wish: str, outcome: Optional[str]) -> PrincipleScore:
        words = wish.split()
        has_number = any(char.isdigit() for char in wish)
        has_deadline = any(word in wish.lower() for word in ["by", "until", "before", "within"])
        specific_verbs = ["complete", "finish", "achieve", "reach", "build", "create", "learn"]
        has_specific_verb = any(v in wish.lower() for v in specific_verbs)

        score = 3
        if len(words) >= 5:
            score += 1
        if has_number or has_deadline:
            score += 1
        if has_specific_verb:
            score = min(5, score)
        if len(words) < 3:
            score = max(1, score - 2)

        return PrincipleScore(
            score=min(5, max(1, score)),
            status=self._score_to_status(score),
            feedback=self._get_clarity_feedback(score, wish),
            improvement=PRINCIPLE_DESCRIPTIONS["clarity"]["improvement_template"] if score < 4 else None
        )

    def _score_challenge(self, confidence: Optional[int]) -> PrincipleScore:
        if confidence is None:
            return PrincipleScore(
                score=3,
                status=ScoreStatus.OKAY,
                feedback="Confidence level not assessed. Aim for 70-90% confidence.",
                improvement="On a scale of 1-10, how confident are you?"
            )
        if 7 <= confidence <= 9:
            return PrincipleScore(score=5, status=ScoreStatus.EXCELLENT, feedback="Perfect challenge level — stretching but achievable")
        elif 6 <= confidence <= 10:
            return PrincipleScore(score=4, status=ScoreStatus.GOOD, feedback="Good challenge level")
        elif 4 <= confidence <= 5:
            return PrincipleScore(score=3, status=ScoreStatus.OKAY, feedback="Might be too challenging", improvement="Consider breaking into smaller milestones")
        else:
            return PrincipleScore(score=2, status=ScoreStatus.NEEDS_WORK, feedback="Either too easy or too hard", improvement=PRINCIPLE_DESCRIPTIONS["challenge"]["improvement_template"])

    def _score_commitment(self, has_why: bool, outcome: Optional[str]) -> PrincipleScore:
        score = 3
        if has_why:
            score += 1
        if outcome and len(outcome.split()) > 20:
            score += 1
        return PrincipleScore(
            score=min(5, score),
            status=self._score_to_status(score),
            feedback="Strong emotional connection" if score >= 4 else "Consider adding more personal meaning",
            improvement=PRINCIPLE_DESCRIPTIONS["commitment"]["improvement_template"] if score < 4 else None
        )

    def _score_feedback(self, has_milestones: bool) -> PrincipleScore:
        score = 4 if has_milestones else 2
        return PrincipleScore(
            score=score,
            status=self._score_to_status(score),
            feedback="Clear progress tracking" if score >= 4 else "Weekly milestones would help",
            improvement=PRINCIPLE_DESCRIPTIONS["feedback"]["improvement_template"] if score < 4 else None
        )

    def _score_complexity(self, wish: str, timeframe: str) -> PrincipleScore:
        long_timeframes = ["6_months", "1_year"]
        short_timeframes = ["1_month", "quarterly", "3_months"]
        word_count = len(wish.split())
        score = 4
        if timeframe in long_timeframes and word_count < 5:
            score = 3
        elif timeframe in short_timeframes and word_count > 20:
            score = 3
        return PrincipleScore(
            score=score,
            status=self._score_to_status(score),
            feedback="Appropriate scope for timeframe",
            improvement=PRINCIPLE_DESCRIPTIONS["complexity"]["improvement_template"] if score < 4 else None
        )

    def _score_to_status(self, score: int) -> ScoreStatus:
        if score >= 5:
            return ScoreStatus.EXCELLENT
        elif score >= 4:
            return ScoreStatus.GOOD
        elif score >= 3:
            return ScoreStatus.OKAY
        return ScoreStatus.NEEDS_WORK

    def _get_clarity_feedback(self, score: int, wish: str) -> str:
        if score >= 5:
            return "Specific goal with clear target and timeline"
        elif score >= 4:
            return "Specific goal with minor room for clarity"
        elif score >= 3:
            return "Somewhat specific — adding deadline or measurement would help"
        return "Goal needs more specificity"

    def _build_validation_prompt(
        self, wish: str, outcome: Optional[str], obstacle: Optional[str],
        if_then: Optional[Dict], future_you: Optional[str], timeframe: str
    ) -> str:
        context = [f"Goal: {wish}"]
        if outcome:
            context.append(f"Outcome visualization: {outcome}")
        if obstacle:
            context.append(f"Primary obstacle: {obstacle}")
        if if_then:
            context.append(f"If-Then plan: WHEN {if_then.get('when', '...')}, THEN {if_then.get('then', '...')}")
        if future_you:
            context.append(f"Future self visualization: {future_you}")
        context.append(f"Timeframe: {timeframe}")

        return f"""Validate this goal against Locke-Latham's 5 principles.

{chr(10).join(context)}

For each principle, provide:
1. Score (1-5)
2. Brief feedback
3. Improvement suggestion if score < 4

Principles:
- CLARITY: Specific, measurable, time-bound
- CHALLENGE: Stretching but achievable (70-90% confidence)
- COMMITMENT: Emotional investment, personal meaning
- FEEDBACK: Clear progress indicators
- COMPLEXITY: Right-sized for timeframe

Return JSON:
{{
  "clarity": {{"score": 1-5, "feedback": "...", "improvement": null|"..."}},
  "challenge": {{"score": 1-5, "feedback": "...", "improvement": null|"..."}},
  "commitment": {{"score": 1-5, "feedback": "...", "improvement": null|"..."}},
  "feedback": {{"score": 1-5, "feedback": "...", "improvement": null|"..."}},
  "complexity": {{"score": 1-5, "feedback": "...", "improvement": null|"..."}},
  "strengths": ["..."],
  "priority_improvement": {{"principle": "...", "suggestion": "...", "impact": "..."}}
}}"""

    def _parse_validation_response(self, response: str) -> LockeLathameValidation:
        import json
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(response[start:end])
                scores = []
                for principle in ["clarity", "challenge", "commitment", "feedback", "complexity"]:
                    p_data = data.get(principle, {})
                    score = PrincipleScore(
                        score=p_data.get("score", 3),
                        status=self._score_to_status(p_data.get("score", 3)),
                        feedback=p_data.get("feedback", ""),
                        improvement=p_data.get("improvement")
                    )
                    scores.append(score)
                total = sum(s.score for s in scores)
                percentage = (total / 25) * 100
                overall = "strong" if total >= 20 else "solid" if total >= 15 else "needs_work"
                return LockeLathameValidation(
                    clarity=scores[0],
                    challenge=scores[1],
                    commitment=scores[2],
                    feedback=scores[3],
                    complexity=scores[4],
                    total_score=total,
                    percentage=percentage,
                    overall_status=overall,
                    strengths=data.get("strengths", []),
                    priority_improvement=data.get("priority_improvement")
                )
        except Exception:
            pass
        return self.validate_sync("placeholder", timeframe="3_months")


def format_validation_result(validation: LockeLathameValidation, preferred_name: str = "friend") -> str:
    emoji = "🌟" if validation.total_score >= 20 else "💪" if validation.total_score >= 15 else "📝"
    lines = [f"**Goal Score: {validation.total_score}/25** {emoji}\n"]

    for name, score in [
        ("Clarity", validation.clarity),
        ("Challenge", validation.challenge),
        ("Commitment", validation.commitment),
        ("Feedback", validation.feedback),
        ("Complexity", validation.complexity)
    ]:
        icon = "✅" if score.score >= 4 else "⚠️" if score.score >= 3 else "❌"
        lines.append(f"{icon} **{name}**: {score.feedback}")

    if validation.total_score >= 20:
        lines.append(f"\nStrong goal, {preferred_name}. Your Future Self approves. ✨")
    elif validation.total_score >= 15:
        if validation.priority_improvement:
            lines.append(f"\nSolid foundation! One tweak would make it stronger:")
            lines.append(f"→ {validation.priority_improvement.get('suggestion', '')}")
    else:
        if validation.priority_improvement:
            lines.append(f"\nLet's strengthen this before we commit:")
            lines.append(f"→ {validation.priority_improvement.get('suggestion', '')}")

    lines.append(f"\n_{validation.research_note}_")
    return "\n".join(lines)
