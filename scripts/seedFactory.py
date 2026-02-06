import json
import random
import uuid
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

#Faker + Seeding to ensure consistent results with same config file.
fake = Faker()
Faker.seed(3)
random.seed(3)

OUTPUT_DIR = Path(__file__).parent / "seeding"

#we use this to put the constants into variables
#eg PRODUCT_TEMPLATES
with open(OUTPUT_DIR / "config.json", encoding="utf-8") as f:
    _cfg = json.load(f)
    for key, value in _cfg.items():
        globals()[key.upper()] = value


def gen_id(_prefix: str = "") -> str:
    return str(uuid.uuid4())


def pick(options: list) -> any:
    return random.choice(options)


def maybe(options: list, prob: float = 0.7) -> str | None:
    return pick(options) if random.random() < prob else None


def gen_brand() -> str:
    return f"{pick(BRAND_ADJECTIVES)} {pick(BRAND_NOUNS)}"


def distribute_percentages(n: int) -> list[int]:
    #distributes by number of cuts eg
    # n = 2 -> [20, 80]
    if n == 1:
        return [100]
    
    cuts = sorted(random.sample(range(1, 100), n - 1))
    segments = []
    segments.append(cuts[0])
    for i in range(1, len(cuts)):
        segments.append(cuts[i] - cuts[i - 1])
    segments.append(100 - cuts[-1])
    
    return segments


def generate_products() -> list[dict]:
    products = []
    for category, count in CATEGORY_DISTRIBUTION.items():
        templates = PRODUCT_TEMPLATES[category]
        for i in range(count):
            brand = gen_brand()
            products.append({
                "product_id": gen_id("prod"),
                "name": pick(templates).format(brand),
                "category": category,
                "brand": brand,
                "description": pick(DESCRIPTIONS["product"]).format(category),
                "image": f"" #Add later?
            })
    return products


def generate_stages(products: list[dict]) -> list[dict]:
    stages = []
    for p in products:
        base = fake.date_between(start_date="-2y", end_date="-6m")
        for sequence_order, stage_type in enumerate(STAGE_TYPES, 1):
            start = base + timedelta(days=(sequence_order - 1) * 30)
            stages.append({
                "stage_id": gen_id("stg"),
                "product_id": p["product_id"],
                "stage_type": stage_type,
                "location_country": pick(COUNTRIES),
                "location_region": fake.city(),
                "start_date": start.isoformat(),
                "end_date": (start + timedelta(days=random.randint(5, 25))).isoformat(),
                "description": pick(DESCRIPTIONS["stage"]),
                "sequence_order": sequence_order
            })
    return stages


def generate_input_shares(products: list[dict]) -> list[dict]:
    inputs = []
    for p in products:
        selected = random.sample(INPUT_NAMES, k=random.randint(2, 4))
        percentages = distribute_percentages(len(selected))
        for i in range(len(selected)):
            inputs.append({
                "input_id": gen_id("inp"),
                "product_id": p["product_id"],
                "input_name": selected[i],
                "country": pick(COUNTRIES),
                "percentage": percentages[i],
                "notes": maybe(DESCRIPTIONS["input_notes"], 0.5)
            })
    return inputs


def generate_claims(products: list[dict]) -> list[dict]:
    claims = []
    for p in products:
        for claim_type in random.sample(CLAIM_TYPES, k=random.randint(1, 3)):
            confidence = pick(CONFIDENCE_LABELS)
            claims.append({
                "claim_id": gen_id("clm"),
                "product_id": p["product_id"],
                "claim_type": claim_type,
                "claim_text": f"This product is {claim_type.replace('_', ' ')}.",
                "confidence_label": confidence,
                "rationale": maybe(CLAIM_RATIONALES[confidence], 0.7)
            })
    return claims


def generate_evidence(stages: list[dict], claims: list[dict], count: int) -> list[dict]:
    stage_ids = [s["stage_id"] for s in stages]
    claim_ids = [c["claim_id"] for c in claims]
    evidence = []
    for i in range(count):
        link_stage = random.random() > 0.4
        evidence.append({
            "evidence_id": gen_id("evd"),
            "stage_id": pick(stage_ids) if link_stage else None,
            "claim_id": pick(claim_ids) if not link_stage else None,
            "type": pick(EVIDENCE_TYPES),
            "issuer": pick(EVIDENCE_ISSUERS),
            "date": fake.date_between(start_date="-1y", end_date="today").isoformat(),
            "summary": pick(DESCRIPTIONS["evidence_summary"]),
            "file_reference": f"" #Add when we decide how to do evidence management
        })
    return evidence


def generate_issues(products: list[dict], count: int) -> list[dict]:
    issues = []
    for i in range(count):
        issue_type = pick(ISSUE_TYPES)
        status = pick(ISSUE_STATUSES)
        issues.append({
            "issue_id": gen_id("iss"),
            "product_id": pick(products)["product_id"],
            "reported_by": gen_id("usr") if random.random() > 0.2 else None,
            "type": issue_type,
            "description": pick(ISSUE_DESCRIPTIONS[issue_type]),
            "status": status,
            "resolution_note": pick(DESCRIPTIONS["resolution_notes"]) if status in ["resolved", "dismissed"] else None
        })
    return issues

def generate_change_logs(products: list[dict], stages: list[dict], claims: list[dict]) -> list[dict]:
    things = {
        "product": [p["product_id"] for p in products],
        "stage": [s["stage_id"] for s in stages],
        "claim": [c["claim_id"] for c in claims],
    }
    logs = []
    for entity_type, ids in things.items():
        for entity_id in random.sample(ids, min(10, len(ids))):
            logs.append({
                "log_id": gen_id("log"),
                "entity_type": entity_type,
                "entity_id": entity_id,
                "changed_by": gen_id("usr") if random.random() > 0.3 else None,
                "change_summary": pick(DESCRIPTIONS["change_log_summaries"])
            })
    return logs

def generate_missions(products: list[dict]) -> list[dict]:
    #will discuss further on this implementation
    pass


def save_json(data: list[dict], filename: str) -> None:
    with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"{filename} {len(data)} record")


def main():
    products = generate_products()
    stages = generate_stages(products)
    claims = generate_claims(products)

    data = {
        "products.json": products,
        "stages.json": stages,
        "input_shares.json": generate_input_shares(products),
        "claims.json": claims,
        "evidence.json": generate_evidence(stages, claims, COUNTS["evidence"]),
        "issues.json": generate_issues(products, COUNTS["issues"]),
        "change_logs.json": generate_change_logs(products, stages, claims),
    }

    for filename, records in data.items():
        save_json(records, filename)



if __name__ == "__main__":
    main()
