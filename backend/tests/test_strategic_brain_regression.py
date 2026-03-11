"""
Strategic Brain — Regression Test Suite
Runs the full flow against a live server on localhost:8099.

Usage:
    ENVIRONMENT=development CLERK_SECRET_KEY="" uvicorn app.main:app --port 8099 &
    python tests/test_strategic_brain_regression.py
"""
import json
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

BASE = "http://127.0.0.1:8099/api/v1/strategic-brain"
passed = 0
failed = 0
created_ids = {}


def req(method: str, path: str, body: dict = None, timeout: int = 60) -> dict:
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read())


def check(name: str, ok: bool, detail: str = ""):
    global passed, failed
    status = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    else:
        failed += 1
    suffix = f"  ({detail})" if detail else ""
    print(f"  [{status}] {name}{suffix}")


def test_health():
    print("\n0. Health check")
    try:
        with urllib.request.urlopen("http://127.0.0.1:8099/health", timeout=5) as r:
            data = json.loads(r.read())
        check("Server healthy", data.get("status") == "healthy")
    except Exception as e:
        check("Server healthy", False, str(e))
        print("\n  Server not running. Start it with:")
        print('  ENVIRONMENT=development CLERK_SECRET_KEY="" uvicorn app.main:app --port 8099')
        sys.exit(1)


def test_set_constraints():
    print("\n1. Set constraints")
    r = req("PATCH", "/constraints", {
        "weekly_hours_available": 15,
        "monthly_budget": 500,
        "health_limits": "RSI in wrists, limit typing to 4h/day",
        "risk_tolerance": "low",
    })
    check("PATCH /constraints returns success", r["success"])
    check("weekly_hours_available saved", r["data"].get("weekly_hours_available") == 15)
    check("risk_tolerance saved", r["data"].get("risk_tolerance") == "low")

    r2 = req("GET", "/constraints")
    check("GET /constraints returns saved values", r2["data"]["monthly_budget"] == 500)
    check("health_limits persisted", "RSI" in (r2["data"].get("health_limits") or ""))


def test_set_anti_goals():
    print("\n2. Set anti-goals")
    anti = [
        "No client services or consulting",
        "No projects requiring >$1000 upfront",
        "Avoid anything that needs a team of 5+",
    ]
    r = req("PATCH", "/anti-goals", {"anti_goals": anti})
    check("PATCH /anti-goals returns success", r["success"])
    check("3 anti-goals stored", len(r["data"]["anti_goals"]) == 3)


def test_add_distraction_rule():
    print("\n3. Add distraction rule")
    r = req("POST", "/rules", {
        "rule_name": "No new projects until current goal > 30%",
        "condition": "Active goals are below 30% progress",
        "action": "Reject new project ideas and focus on existing goals",
        "rule_type": "custom",
    })
    check("POST /rules returns success", r["success"])
    check("Rule ID returned", bool(r["data"].get("id")))
    created_ids["rule"] = r["data"]["id"]

    r2 = req("GET", "/rules")
    check("GET /rules lists active rules", len(r2["data"]) >= 1)
    names = [x["rule_name"] for x in r2["data"]]
    check("Created rule appears in list", any("No new projects" in n for n in names))


def test_score_opportunity_aligned():
    print("\n4. Score opportunity (aligned — should score well)")
    r = req("POST", "/opportunities/score", {
        "description": "Build a simple landing page with email capture for my existing AI app. Takes 2 hours, no cost, uses skills I already have.",
    })
    check("POST /opportunities/score returns success", r["success"])
    scores = r["data"].get("scores", {})
    check("Scores JSON has 6 dimensions", all(
        k in scores for k in ["revenue_potential", "strategic_fit", "effort_complexity",
                               "skill_match", "time_to_first_win", "risk_regret_cost"]
    ))
    opp_id = r["data"].get("opportunity_id")
    check("opportunity_id returned", bool(opp_id))
    created_ids["opp_aligned"] = opp_id

    effort = scores.get("effort_complexity", 0)
    check("Effort/complexity score >= 6 (easy task)", effort >= 6, f"got {effort}")

    conflicts = scores.get("anti_goal_conflicts", [])
    check("No anti-goal conflicts for aligned opportunity", len(conflicts) == 0, str(conflicts))


def test_score_opportunity_conflicting():
    print("\n5. Score opportunity (conflicting — should score low, flag warnings)")
    r = req("POST", "/opportunities/score", {
        "description": "Start a consulting agency offering AI strategy to enterprises. Needs a team of 8, $5000 upfront investment, 30 hrs/week commitment for 6 months.",
    })
    check("POST /opportunities/score returns success", r["success"])
    scores = r["data"].get("scores", {})
    opp_id = r["data"].get("opportunity_id")
    created_ids["opp_conflict"] = opp_id

    total = sum(scores.get(k, 0) for k in [
        "revenue_potential", "strategic_fit", "effort_complexity",
        "skill_match", "time_to_first_win", "risk_regret_cost"
    ]) / 6.0
    check("Total score <= 5 (bad fit)", total <= 5, f"got {total:.1f}")

    effort = scores.get("effort_complexity", 10)
    check("Effort/complexity <= 4 (exceeds hours + budget)", effort <= 4, f"got {effort}")

    risk = scores.get("risk_regret_cost", 10)
    check("Risk score <= 4 (low tolerance, high risk idea)", risk <= 4, f"got {risk}")

    conflicts = scores.get("anti_goal_conflicts", [])
    check("Anti-goal conflicts detected (>= 1)", len(conflicts) >= 1, str(conflicts))

    constraint_warns = scores.get("constraint_warnings", [])
    check("Constraint warnings detected (>= 1)", len(constraint_warns) >= 1, str(constraint_warns))

    verdict = scores.get("verdict", "")
    check("Verdict is 'pass' (don't pursue)", verdict == "pass", f"got '{verdict}'")


def test_verify_opportunities_persisted():
    print("\n6. Verify opportunities persisted")
    r = req("GET", "/opportunities")
    check("GET /opportunities returns list", r["success"] and isinstance(r["data"], list))
    ids = [o["id"] for o in r["data"]]
    check("Aligned opportunity in list", created_ids.get("opp_aligned") in ids)
    check("Conflicting opportunity in list", created_ids.get("opp_conflict") in ids)

    if created_ids.get("opp_aligned"):
        r2 = req("GET", f"/opportunities/{created_ids['opp_aligned']}")
        check("GET single opportunity by ID works", r2["success"])
        check("Opportunity has description", bool(r2["data"].get("description")))


def test_update_opportunity_status():
    print("\n7. Update opportunity status")
    if not created_ids.get("opp_aligned"):
        check("Skip — no opportunity to update", False)
        return
    r = req("PATCH", f"/opportunities/{created_ids['opp_aligned']}", {"status": "pursuing"})
    check("PATCH status returns success", r["success"])
    check("Status updated to 'pursuing'", r["data"]["status"] == "pursuing")


def test_log_decision():
    print("\n8. Log a decision")
    r = req("POST", "/decisions", {
        "decision": "Focus exclusively on the AI app for the next 90 days",
        "why": "Spreading attention across projects kills momentum",
        "expected_outcome": "App reaches 1000 users within 90 days",
        "review_days": 30,
        "tags": ["focus", "90-day-sprint"],
    })
    check("POST /decisions returns success", r["success"])
    check("Decision ID returned", bool(r["data"].get("id")))
    check("Review date returned", bool(r["data"].get("review_date")))
    created_ids["decision"] = r["data"]["id"]

    r2 = req("GET", "/decisions")
    check("GET /decisions returns list", r2["success"] and isinstance(r2["data"], list))
    found = [d for d in r2["data"] if d["id"] == created_ids["decision"]]
    check("Logged decision appears in list", len(found) == 1)
    check("Tags persisted", found[0].get("tags") == ["focus", "90-day-sprint"] if found else False)


def test_open_experiment():
    print("\n9. Open an experiment")
    r = req("POST", "/experiments", {
        "hypothesis": "If I add a 'quick demo' video to the landing page, signups will increase by 20%",
        "action": "Record a 60-second demo video and A/B test for 2 weeks",
        "tags": ["conversion", "landing-page"],
    })
    check("POST /experiments returns success", r["success"])
    check("Experiment ID returned", bool(r["data"].get("id")))
    created_ids["experiment"] = r["data"]["id"]

    r2 = req("GET", "/experiments?status=open")
    check("GET /experiments?status=open returns list", r2["success"])
    ids = [e["id"] for e in r2["data"]]
    check("New experiment in open list", created_ids["experiment"] in ids)


def test_anti_goal_conflict_check():
    print("\n10. Anti-goal conflict check endpoint")
    proposal = urllib.parse.quote("Hire 6 contractors to build a consulting practice")
    r = req("GET", f"/anti-goals/check?proposal={proposal}")
    check("GET /anti-goals/check returns success", r["success"])
    check("has_conflicts is true", r["data"]["has_conflicts"] is True)
    check("At least 1 conflict listed", len(r["data"]["conflicts"]) >= 1)


def test_constraints_validation():
    print("\n11. Constraints validation")
    try:
        r = req("PATCH", "/constraints", {"risk_tolerance": "yolo"})
        check("Invalid risk_tolerance rejected", False, "expected 422")
    except urllib.error.HTTPError as e:
        check("Invalid risk_tolerance rejected (422)", e.code == 422)


def test_decision_review_loop():
    print("\n13. Decision Review Loop — full lifecycle")

    # 13a. Create a decision with review_date = today (review_days=0)
    r = req("POST", "/decisions", {
        "decision": "Switch landing page CTA from 'Sign Up' to 'Start Free'",
        "why": "A/B test data shows action-oriented CTAs convert 15% better",
        "expected_outcome": "Signup rate increases from 3% to 4.5% within 2 weeks",
        "review_days": 0,
        "tags": ["conversion", "landing-page"],
    })
    check("Create decision with review_date=today", r["success"])
    review_decision_id = r["data"]["id"]
    created_ids["review_decision"] = review_decision_id
    check("Review date is today", r["data"]["review_date"] == time.strftime("%Y-%m-%d"))

    # 13b. Verify it appears in pending-reviews
    r2 = req("GET", "/decisions/pending-reviews")
    check("GET /decisions/pending-reviews returns success", r2["success"])
    pending_ids = [d["id"] for d in r2["data"]]
    check("New decision appears in pending-reviews", review_decision_id in pending_ids)

    pending_entry = [d for d in r2["data"] if d["id"] == review_decision_id][0]
    check("Pending entry has status pending_review", pending_entry["status"] == "pending_review")
    check("Pending entry has expected_outcome", "4.5%" in (pending_entry.get("expected_outcome") or ""))

    # 13c. Submit review with actual outcome
    r3 = req("POST", f"/decisions/{review_decision_id}/review", {
        "actual_outcome": "Signup rate increased from 3% to 4.1% — good but under the 4.5% target. Mobile performed better than desktop.",
    })
    check("POST /decisions/{id}/review returns success", r3["success"])
    check("decision_id matches", r3["data"].get("decision_id") == review_decision_id)
    check("learning_summary returned", bool(r3["data"].get("learning_summary")))
    check("is_significant field present", "is_significant" in r3["data"])

    # 13d. Verify decision updated in main list
    r4 = req("GET", "/decisions")
    reviewed = [d for d in r4["data"] if d["id"] == review_decision_id]
    check("Decision found in list after review", len(reviewed) == 1)
    check("Status updated to 'reviewed'", reviewed[0]["status"] == "reviewed")
    check("actual_outcome persisted", "4.1%" in (reviewed[0].get("actual_outcome") or ""))
    check("Tags still intact after review", reviewed[0].get("tags") == ["conversion", "landing-page"])

    # 13e. Verify it no longer appears in pending-reviews
    r5 = req("GET", "/decisions/pending-reviews")
    check("Reviewed decision gone from pending-reviews",
          review_decision_id not in [d["id"] for d in r5["data"]])

    # 13f. If learning was significant, verify auto-experiment created
    if r3["data"].get("experiment_id"):
        created_ids["review_experiment"] = r3["data"]["experiment_id"]
        r6 = req("GET", "/experiments?status=open")
        exp_ids = [e["id"] for e in r6["data"]]
        check("Auto-generated experiment exists in open list", r3["data"]["experiment_id"] in exp_ids)

        exp_detail = [e for e in r6["data"] if e["id"] == r3["data"]["experiment_id"]]
        if exp_detail:
            check("Experiment has hypothesis", bool(exp_detail[0].get("hypothesis")))
            check("Experiment tagged as decision-review",
                  "decision-review" in (exp_detail[0].get("tags") or []))
    else:
        check("No experiment (learning not significant — acceptable)", True)

    # 13g. Verify original section-8 decision (review_days=30) is NOT in pending
    if created_ids.get("decision"):
        r7 = req("GET", "/decisions/pending-reviews")
        future_ids = [d["id"] for d in r7["data"]]
        check("Future-dated decision not in pending-reviews", created_ids["decision"] not in future_ids)


def test_cleanup_rule():
    print("\n14. Cleanup — delete rule, verify gone")
    if not created_ids.get("rule"):
        check("Skip — no rule to delete", False)
        return
    r = req("DELETE", f"/rules/{created_ids['rule']}")
    check("DELETE /rules/{id} returns success", r["success"])

    r2 = req("GET", "/rules")
    ids = [x["id"] for x in r2["data"]]
    check("Deleted rule no longer in list", created_ids["rule"] not in ids)


def main():
    global passed, failed
    t0 = time.time()

    test_health()
    test_set_constraints()
    test_set_anti_goals()
    test_add_distraction_rule()
    test_score_opportunity_aligned()
    test_score_opportunity_conflicting()
    test_verify_opportunities_persisted()
    test_update_opportunity_status()
    test_log_decision()
    test_open_experiment()
    test_anti_goal_conflict_check()
    test_constraints_validation()
    test_decision_review_loop()
    test_cleanup_rule()

    elapsed = time.time() - t0
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"  {passed}/{total} passed, {failed} failed  ({elapsed:.1f}s)")
    print(f"{'='*60}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
