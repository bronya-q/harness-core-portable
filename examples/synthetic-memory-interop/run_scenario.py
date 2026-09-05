#!/usr/bin/env python3
"""Run the synthetic memory interoperability contract fixture.

This is a deterministic local contract test. It does not import or impersonate
rawmem/memdsl and performs no network, model, database, or external action.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCENARIO = ROOT / "scenario.json"
TRACE_JSON = ROOT / "expected-trace.json"
TRACE_MD = ROOT / "expected-trace.md"


def _digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load() -> dict:
    return json.loads(SCENARIO.read_text(encoding="utf-8"))


def _index(rows: list[dict], key: str) -> dict[str, dict]:
    return {row[key]: row for row in rows}


def build_trace(data: dict) -> dict:
    events = _index(data["events"], "event_id")
    candidates = _index(data["candidates"], "candidate_id")
    reviews = _index(data["reviews"], "candidate_id")
    memories = {row["memory_id"]: row for row in data["candidates"] if row.get("memory_id")}
    checks: list[dict] = []

    def check(check_id: str, ok: bool, detail: str) -> None:
        checks.append({"check_id": check_id, "ok": bool(ok), "detail": detail})

    for event in data["events"]:
        check(
            "hash:" + event["event_id"],
            event["content_hash"] == _digest(event["quote"]),
            "quoted source text matches content_hash",
        )

    for candidate in data["candidates"]:
        ref = candidate["source_ref"]
        source = events.get(ref["event_id"])
        ok = bool(source) and all(
            ref[field] == source[field]
            for field in ("ledger_id", "event_id", "content_hash", "quote")
        )
        check(
            "traceability:" + candidate["candidate_id"],
            ok,
            "%s traces to %s/%s"
            % (candidate["candidate_id"], ref["ledger_id"], ref["event_id"]),
        )
        review = reviews.get(candidate["candidate_id"])
        check(
            "review:" + candidate["candidate_id"],
            bool(review)
            and review["decision"] == candidate["status"]
            and review["result_memory_id"] == candidate["memory_id"],
            "%s has an explicit human review result" % candidate["candidate_id"],
        )

    requests = []
    for request in data["requests"]:
        expected = request["expected"]
        provided = expected.get("provided_memory_ids", [])
        excluded = expected.get("excluded_memory_ids", {})
        effects = expected.get("memory_effects", {})
        available = set(request.get("available_memory_ids", []))

        check(
            "available:" + request["request_id"],
            all(memory_id in available for memory_id in provided),
            "every provided memory is available in this phase",
        )
        check(
            "known-memory:" + request["request_id"],
            all(memory_id in memories for memory_id in provided),
            "every provided memory has an approved fixture record",
        )

        trace_row = {
            "request_id": request["request_id"],
            "phase": request["phase"],
            "input": request["text"],
            "provided_memory_ids": provided,
            "memory_effects": effects,
            "excluded_memory_ids": excluded,
            "response_mode": expected["response_mode"],
            "response": expected["response"],
            "permission": expected["permission"],
            "executed": expected.get("executed"),
            "creates_candidate": expected.get("creates_candidate"),
        }
        requests.append(trace_row)

    pending = next(row for row in data["requests"] if row["phase"] == "before_approval")
    check(
        "pending-not-active",
        not pending["expected"]["provided_memory_ids"],
        "candidate-001 is visible for review but is not provided as active memory",
    )

    override = next(row for row in data["requests"] if row["phase"] == "current_turn_override")
    check(
        "current-turn-does-not-rewrite-memory",
        override["expected"].get("creates_candidate") is False,
        "one-turn detail request changes this response without creating durable memory",
    )
    check(
        "current-intent-overrides-soft-preference",
        override["expected"]["memory_effects"].get("memory-001")
        == "overridden_by_current_intent"
        and override["expected"]["response_mode"] == "detailed",
        "memory-001 is observed but does not mechanically shorten the requested explanation",
    )

    technical = next(row for row in data["requests"] if row["phase"] == "contextual_preference")
    check(
        "specific-preference-wins-without-superseding",
        technical["expected"]["memory_effects"].get("memory-002")
        == "selected_specific_preference"
        and not candidates["candidate-002"].get("supersedes"),
        "technical preference coexists with the general concise preference",
    )

    action = next(row for row in data["requests"] if row["phase"] == "permission_separation")
    check(
        "memory-is-not-permission",
        action["expected"]["permission"] == "confirmation_required"
        and action["expected"].get("executed") is False,
        "remembered willingness to prepare a release does not authorize publishing",
    )

    correction = candidates["candidate-004"]
    after = next(row for row in data["requests"] if row["phase"] == "after_correction")
    check(
        "superseded-is-auditable-not-active",
        correction.get("supersedes") == ["memory-001"]
        and after["expected"]["excluded_memory_ids"].get("memory-001") == "superseded"
        and "memory-001" not in after["expected"]["provided_memory_ids"],
        "memory-001 remains in fixture history but is excluded after memory-004 approval",
    )

    return {
        "schema_version": "hcp.synthetic-memory-trace.v1",
        "scenario": data["schema_version"],
        "integration_status": data["integration_status"],
        "boundaries": data["boundaries"],
        "reviews": data["reviews"],
        "requests": requests,
        "checks": checks,
        "summary": {
            "ok": all(row["ok"] for row in checks),
            "passed": sum(1 for row in checks if row["ok"]),
            "total": len(checks),
        },
    }


def render_markdown(trace: dict) -> str:
    rows = []
    for item in trace["requests"]:
        provided = ", ".join(item["provided_memory_ids"]) or "—"
        effects = ", ".join("%s=%s" % pair for pair in item["memory_effects"].items()) or "—"
        excluded = ", ".join("%s=%s" % pair for pair in item["excluded_memory_ids"].items()) or "—"
        executed = "—" if item["executed"] is None else str(item["executed"]).lower()
        rows.append(
            "| {request_id} | {phase} | {provided} | {effects} | {excluded} | "
            "{response_mode} | {permission} | {executed} |".format(
                request_id=item["request_id"],
                phase=item["phase"],
                provided=provided,
                effects=effects,
                excluded=excluded,
                response_mode=item["response_mode"],
                permission=item["permission"],
                executed=executed,
            )
        )
    review_rows = [
        "| {review_id} | {candidate_id} | {decision} | {result_memory_id} | {reviewed_by} |".format(**item)
        for item in trace["reviews"]
    ]
    answer_sections = []
    for item in trace["requests"]:
        answer_sections.append(
            "### `%s`\n\n**输入：** %s\n\n**实际提供给模型：** %s\n\n**预期回答：** %s"
            % (
                item["request_id"],
                item["input"],
                ", ".join(item["provided_memory_ids"]) or "无",
                item["response"],
            )
        )
    check_rows = [
        "- [%s] `%s` — %s" % ("x" if row["ok"] else " ", row["check_id"], row["detail"])
        for row in trace["checks"]
    ]
    return """# Synthetic Memory Interop Expected Trace

> Generated from `scenario.json` by `run_scenario.py`. This is a deterministic
> contract fixture, not evidence of a live rawmem or memdsl integration.

## Review results

| Review | Candidate | Decision | Result memory | Reviewed by |
|---|---|---|---|---|
%s

## Runtime trace

| Request | Phase | Memories actually provided to model | Effect in this turn | Excluded | Response mode | Permission | Executed |
|---|---|---|---|---|---|---|---|
%s

## Inputs and expected answers

%s

## Checks

%s

## Result

```json
%s
```
""" % (
        "\n".join(review_rows),
        "\n".join(rows),
        "\n\n".join(answer_sections),
        "\n".join(check_rows),
        json.dumps(trace["summary"], ensure_ascii=False, indent=2),
    )


def main() -> int:
    trace = build_trace(_load())
    TRACE_JSON.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    TRACE_MD.write_text(render_markdown(trace), encoding="utf-8")
    for row in trace["checks"]:
        print(("PASS" if row["ok"] else "FAIL") + " " + row["check_id"])
    print(json.dumps(trace["summary"], ensure_ascii=False))
    return 0 if trace["summary"]["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
