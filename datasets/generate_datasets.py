"""Generates the 10 frozen incident scenarios (experiment.md §6).

Run once, by hand, before Phase 2: `python -m relationship_density.datasets.generate_datasets`
The resulting incident_01.json .. incident_10.json are then frozen —
this script is not re-run as part of the experiment itself, per
experiment.md's instruction that the corpus is not regenerated after
freezing.

Partition rule (locked to keep dataset-level redundancy out of the
picture, so any redundancy later measured is attributable to agent
communication, not to the dataset already containing duplicate
information): each of the ~17-20 expected facts is assigned to
exactly one agent's initial knowledge. No agent starts with a fact
any other agent also starts with.

per_agent_knowledge is stored as a LIST of individual fact strings
per agent (not a joined block of text) — PureAgent (agents/policy.py)
needs to reason about individual facts one at a time.
"""
import json
import random
from pathlib import Path

_OUTPUT_DIR = Path(__file__).parent
_NUM_AGENTS = 8

_INCIDENT_TEMPLATES = [
    {
        "theme": "database connection pool exhaustion",
        "service": "checkout-service",
        "root_cause": "The checkout-service database connection pool was exhausted after a deploy reduced max connections from 100 to 20.",
        "evidence": ["Connection pool metrics show saturation at 20/20 starting 14:03 UTC.",
                     "Error logs show 'connection pool exhausted' first at 14:04 UTC.",
                     "The config diff for the 14:00 UTC deploy shows max_connections changed from 100 to 20."],
        "impact": ["Checkout success rate dropped from 99.2% to 61% between 14:03 and 14:47 UTC.",
                   "Approximately 8,400 checkout attempts failed during the incident window.",
                   "Downstream payment-service saw a 3x retry-storm from checkout-service."],
        "timeline": ["14:00 UTC: deploy of checkout-service v2.14.0 begins.",
                     "14:03 UTC: connection pool saturation begins.",
                     "14:47 UTC: rollback to v2.13.2 completes and pool saturation clears."],
        "dependency": ["checkout-service depends on payment-service for authorization.",
                       "checkout-service depends on inventory-service for stock holds."],
        "mitigation": ["On-call rolled back checkout-service to v2.13.2 at 14:44 UTC.",
                       "max_connections was restored to 100 in the rollback."],
        "regression": ["The same max_connections misconfiguration caused a smaller incident on a staging deploy two weeks earlier."],
        "fix": "Restore max_connections to a value load-tested for peak traffic, and add a pre-deploy config diff check for connection-pool settings.",
        "verification_plan": "Re-run peak-traffic load test against the restored config, and add an alert on connection-pool saturation above 90% for two release cycles.",
    },
    {
        "theme": "cache stampede after TTL misconfiguration",
        "service": "product-catalog-service",
        "root_cause": "A cache TTL misconfiguration caused all product-catalog cache entries to expire simultaneously, triggering a cache stampede against the primary database.",
        "evidence": ["Cache hit rate dropped from 97% to 4% within a 90-second window at 09:15 UTC.",
                     "Primary database CPU spiked to 98% at 09:16 UTC.",
                     "The cache TTL config was set to a fixed absolute timestamp instead of a relative duration in the 09:00 UTC deploy."],
        "impact": ["Product page load latency (p95) rose from 220ms to 4.8s.",
                   "Database read replicas fell behind primary by up to 40 seconds.",
                   "Search-service, which reads from product-catalog-service, returned stale results for 22 minutes."],
        "timeline": ["09:00 UTC: cache-config deploy goes out.",
                     "09:15 UTC: mass cache expiry begins.",
                     "09:37 UTC: cache warm-up script restores hit rate above 90%."],
        "dependency": ["product-catalog-service depends on the shared Redis cluster.",
                       "search-service depends on product-catalog-service for freshness."],
        "mitigation": ["On-call manually triggered the cache warm-up script at 09:30 UTC.",
                       "Database read replicas were temporarily scaled from 3 to 6 nodes."],
        "regression": ["A near-identical TTL misconfiguration was fixed in the pricing-service six months prior; the fix was not applied to product-catalog-service's config template."],
        "fix": "Switch cache TTLs to jittered relative durations and copy the pricing-service TTL-jitter fix into the shared config template.",
        "verification_plan": "Verify TTL jitter is present in the shared config template used by all services, and load-test a simulated mass-expiry scenario in staging.",
    },
    {
        "theme": "DNS resolution failure after provider migration",
        "service": "notification-service",
        "root_cause": "A DNS provider migration left an internal service record unmigrated, causing notification-service to fail resolving auth-service's internal hostname.",
        "evidence": ["DNS query logs show NXDOMAIN responses for auth-service.internal starting 03:12 UTC.",
                     "The DNS migration runbook's service inventory did not include auth-service.internal.",
                     "notification-service error logs show 'failed to resolve host' beginning 03:12 UTC."],
        "impact": ["100% of push and email notifications failed to send between 03:12 and 04:05 UTC.",
                   "Approximately 190,000 notifications were queued and delayed.",
                   "user-service, which also calls auth-service, was unaffected because it caches DNS results for 30 minutes."],
        "timeline": ["03:00 UTC: DNS provider migration begins.",
                     "03:12 UTC: notification-service begins failing DNS resolution.",
                     "04:05 UTC: missing DNS record is manually added and propagates."],
        "dependency": ["notification-service depends on auth-service to validate delivery tokens.",
                       "auth-service's internal hostname is resolved via the internal DNS zone."],
        "mitigation": ["The missing DNS record was manually added to the new provider at 03:58 UTC.",
                       "Queued notifications were replayed starting 04:10 UTC."],
        "regression": ["The DNS migration runbook has caused two prior partial outages from incomplete service inventories."],
        "fix": "Generate the DNS migration service inventory automatically from service-discovery records instead of a manually maintained list.",
        "verification_plan": "Diff the automated service inventory against the manual one used in this migration, and confirm zero discrepancies before the next migration phase.",
    },
]


def _extend_facts(template: dict) -> list:
    facts = []
    facts.append(template["root_cause"])
    facts.extend(template["evidence"])
    facts.extend(template["impact"])
    facts.extend(template["timeline"])
    facts.extend(template["dependency"])
    facts.extend(template["mitigation"])
    facts.extend(template["regression"])
    facts.append(template["fix"])
    facts.append(template["verification_plan"])
    return facts


def _partition_no_overlap(facts: list, num_agents: int, rng: random.Random) -> dict:
    shuffled = list(facts)
    rng.shuffle(shuffled)
    per_agent = {str(i): [] for i in range(num_agents)}
    for index, fact in enumerate(shuffled):
        agent_id = index % num_agents
        per_agent[str(agent_id)].append(fact)
    return per_agent


def generate_all(output_dir: Path = _OUTPUT_DIR) -> None:
    for i in range(10):
        template = _INCIDENT_TEMPLATES[i % len(_INCIDENT_TEMPLATES)]
        scenario_id = f"incident_{i + 1:02d}"
        rng = random.Random(1000 + i)  # fixed, documented seed per scenario

        expected_facts = _extend_facts(template)
        per_agent_knowledge = _partition_no_overlap(expected_facts, _NUM_AGENTS, rng)

        scenario = {
            "scenario_id": scenario_id,
            "theme": template["theme"],
            "service": template["service"],
            "per_agent_knowledge": per_agent_knowledge,  # dict[str, list[str]]
            "expected_facts": expected_facts,
            "ground_truth_sections": {
                "root_cause": template["root_cause"],
                "evidence": " ".join(template["evidence"]),
                "impact": " ".join(template["impact"]),
                "fix": template["fix"],
                "verification_plan": template["verification_plan"],
            },
        }

        path = output_dir / f"{scenario_id}.json"
        with open(path, "w") as f:
            json.dump(scenario, f, indent=2)
        print(f"wrote {path} ({len(expected_facts)} expected facts)")


if __name__ == "__main__":
    generate_all()
