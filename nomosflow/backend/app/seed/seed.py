"""
Seed script: 5 partners, 50 customers, rich payments history.
Run: python -m app.seed.seed
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import date, timedelta, datetime
from decimal import Decimal
import random
from app.database import SessionLocal, engine
from app.models import Partner, Customer, Payment, DunningAction, ChurnScore
from app.database import Base

Base.metadata.create_all(bind=engine)

db = SessionLocal()

if db.query(Partner).first():
    print("✓ Database already seeded — skipping.")
    db.close()
    sys.exit(0)

# ── Partners ───────────────────────────────────────────────────────────────────
partners_data = [
    {
        "name": "Müller Wärmepumpen GmbH",
        "slug": "muller-wp",
        "device_type": "heat_pump",
        "brand_color": "#1D4ED8",
        "logo_url": None,
    },
    {
        "name": "VoltDrive EV Solutions",
        "slug": "voltdrive-ev",
        "device_type": "ev",
        "brand_color": "#059669",
        "logo_url": None,
    },
    {
        "name": "SolarEdge Home Battery",
        "slug": "solaredge-battery",
        "device_type": "battery",
        "brand_color": "#D97706",
        "logo_url": None,
    },
    {
        "name": "NordWind Wärmepumpen",
        "slug": "nordwind-wp",
        "device_type": "heat_pump",
        "brand_color": "#7C3AED",
        "logo_url": None,
    },
    {
        "name": "SpeedCharge Mobility",
        "slug": "speedcharge-ev",
        "device_type": "ev",
        "brand_color": "#DC2626",
        "logo_url": None,
    },
]

partners = []
for pd in partners_data:
    p = Partner(**pd)
    db.add(p)
    db.flush()
    partners.append(p)

db.commit()

# ── Customers ──────────────────────────────────────────────────────────────────
# Columns: name, email, device, city, salary_day, annual_saving, monthly_kwh, contract_start, status, partner_slug
customers_raw = [
    # ── Müller Wärmepumpen (heat_pump) ──────────────────────────────────────
    ("Anna Bergmann",       "anna.bergmann@example.de",     "heat_pump", "Berlin",       25,  180,  8,  "2024-06-15", "active",    "muller-wp"),
    ("Klaus Hoffmann",      "k.hoffmann@example.de",        "heat_pump", "Munich",       28,  210,  1,  "2024-03-01", "active",    "muller-wp"),
    ("Petra Schütz",        "petra.schutz@mail.de",         "heat_pump", "Hamburg",      None,160, 15,  "2024-09-10", "suspended", "muller-wp"),
    ("Thomas Weber",        "t.weber@example.de",           "heat_pump", "Frankfurt",    30,   95,  5,  "2025-01-20", "active",    "muller-wp"),
    ("Maria Keller",        "maria.keller@example.de",      "heat_pump", "Leipzig",      25,  230,  1,  "2023-11-05", "active",    "muller-wp"),
    ("Günter Fischer",      "g.fischer@example.de",         "heat_pump", "Cologne",      None,175, 12,  "2024-07-22", "active",    "muller-wp"),
    ("Sabine Richter",      "s.richter@example.de",         "heat_pump", "Stuttgart",    27,  145,  3,  "2025-02-01", "active",    "muller-wp"),
    ("Michael Braun",       "m.braun@example.de",           "heat_pump", "Berlin",       None,190, None,"2024-04-14", "cancelled", "muller-wp"),
    ("Ursula Lange",        "u.lange@example.de",           "heat_pump", "Munich",       28,  205,  1,  "2024-08-30", "active",    "muller-wp"),
    ("Werner Krüger",       "w.krueger@example.de",         "heat_pump", "Dresden",      25,  165,  5,  "2024-02-10", "active",    "muller-wp"),
    # ── VoltDrive EV ────────────────────────────────────────────────────────
    ("Felix Zimmermann",    "f.zimm@voltdrive.de",          "ev",        "Berlin",       25,  320, 10,  "2024-05-01", "active",    "voltdrive-ev"),
    ("Sophie Müller",       "s.mueller@voltdrive.de",       "ev",        "Hamburg",      None,280, 20,  "2024-10-15", "active",    "voltdrive-ev"),
    ("Lukas Schmidt",       "lukas.s@voltdrive.de",         "ev",        "Frankfurt",    30,  410,  1,  "2024-01-08", "active",    "voltdrive-ev"),
    ("Emma Wagner",         "emma.w@voltdrive.de",          "ev",        "Munich",       25,  295,  5,  "2025-01-15", "active",    "voltdrive-ev"),
    ("Noah Becker",         "noah.b@voltdrive.de",          "ev",        "Cologne",      None,260, 15,  "2024-11-01", "suspended", "voltdrive-ev"),
    ("Lena Meyer",          "lena.m@voltdrive.de",          "ev",        "Stuttgart",    27,  380, 27,  "2024-03-20", "active",    "voltdrive-ev"),
    ("Max Schulz",          "max.s@voltdrive.de",           "ev",        "Berlin",       None,310, None,"2024-06-10", "active",    "voltdrive-ev"),
    ("Hannah Koch",         "h.koch@voltdrive.de",          "ev",        "Düsseldorf",   25,  290,  1,  "2025-02-20", "active",    "voltdrive-ev"),
    ("Tobias Hartmann",     "t.hartmann@voltdrive.de",      "ev",        "Nuremberg",    28,  345,  8,  "2024-07-11", "active",    "voltdrive-ev"),
    ("Melanie Vogel",       "m.vogel@voltdrive.de",         "ev",        "Bonn",         None,275, 22,  "2024-12-01", "active",    "voltdrive-ev"),
    # ── SolarEdge Battery ───────────────────────────────────────────────────
    ("David Krause",        "d.krause@solaredge.de",        "battery",   "Berlin",       None,520, 18,  "2024-02-10", "active",    "solaredge-battery"),
    ("Julia Wolf",          "j.wolf@solaredge.de",          "battery",   "Munich",       28,  480,  1,  "2024-09-01", "active",    "solaredge-battery"),
    ("Stefan Neumann",      "s.neumann@solaredge.de",       "battery",   "Hamburg",      None,490, 10,  "2024-07-05", "cancelled", "solaredge-battery"),
    ("Laura Schwarz",       "l.schwarz@solaredge.de",       "battery",   "Frankfurt",    30,  560,  5,  "2023-12-01", "active",    "solaredge-battery"),
    ("Markus Braun",        "m.braun2@solaredge.de",        "battery",   "Leipzig",      25,  435, 25,  "2024-05-15", "active",    "solaredge-battery"),
    ("Claudia Werner",      "c.werner@solaredge.de",        "battery",   "Cologne",      None,510, 15,  "2024-08-20", "active",    "solaredge-battery"),
    ("Andreas König",       "a.koenig@solaredge.de",        "battery",   "Stuttgart",    27,  470,  3,  "2025-01-05", "active",    "solaredge-battery"),
    ("Ingrid Maier",        "i.maier@solaredge.de",         "battery",   "Berlin",       None,540, None,"2024-03-28", "active",    "solaredge-battery"),
    ("Ralf Bauer",          "r.bauer@solaredge.de",         "battery",   "Heidelberg",   25,  498, 12,  "2024-10-20", "active",    "solaredge-battery"),
    ("Monika Seidel",       "m.seidel@solaredge.de",        "battery",   "Freiburg",     30,  515,  1,  "2024-01-15", "suspended", "solaredge-battery"),
    # ── NordWind Wärmepumpen (heat_pump) ────────────────────────────────────
    ("Björn Petersen",      "b.petersen@nordwind.de",       "heat_pump", "Kiel",         27,  155,  5,  "2024-04-01", "active",    "nordwind-wp"),
    ("Astrid Lindqvist",    "a.lindqvist@nordwind.de",      "heat_pump", "Hamburg",      None,172, 18,  "2024-08-15", "active",    "nordwind-wp"),
    ("Henrik Möller",       "h.moeller@nordwind.de",        "heat_pump", "Lübeck",       25,  140,  1,  "2025-01-10", "active",    "nordwind-wp"),
    ("Sigrid Andersen",     "s.andersen@nordwind.de",       "heat_pump", "Rostock",      28,  185, 28,  "2023-10-01", "active",    "nordwind-wp"),
    ("Lars Eriksson",       "l.eriksson@nordwind.de",       "heat_pump", "Bremen",       None,168, None,"2024-06-20", "cancelled", "nordwind-wp"),
    ("Katrin Brandt",       "k.brandt@nordwind.de",         "heat_pump", "Hannover",     25,  192,  5,  "2024-09-05", "active",    "nordwind-wp"),
    ("Olaf Schneider",      "o.schneider@nordwind.de",      "heat_pump", "Kiel",         30,  148,  1,  "2025-02-15", "active",    "nordwind-wp"),
    ("Brigitte Holm",       "b.holm@nordwind.de",           "heat_pump", "Hamburg",      None,163, 15,  "2024-05-28", "suspended", "nordwind-wp"),
    ("Erik Svensson",       "e.svensson@nordwind.de",       "heat_pump", "Flensburg",    27,  177,  3,  "2024-11-12", "active",    "nordwind-wp"),
    ("Inge Dahl",           "i.dahl@nordwind.de",           "heat_pump", "Lübeck",       25,  158, 25,  "2024-03-07", "active",    "nordwind-wp"),
    # ── SpeedCharge EV ──────────────────────────────────────────────────────
    ("Jonas Weber",         "j.weber@speedcharge.de",       "ev",        "Munich",       28,  355, 10,  "2024-06-01", "active",    "speedcharge-ev"),
    ("Katharina Braun",     "k.braun@speedcharge.de",       "ev",        "Stuttgart",    25,  390,  1,  "2024-02-20", "active",    "speedcharge-ev"),
    ("Niklas Hoffmann",     "n.hoffmann@speedcharge.de",    "ev",        "Frankfurt",    None,300, 20,  "2024-11-15", "active",    "speedcharge-ev"),
    ("Franziska Schmidt",   "f.schmidt@speedcharge.de",     "ev",        "Berlin",       30,  420,  5,  "2023-09-10", "active",    "speedcharge-ev"),
    ("Patrick Müller",      "p.mueller@speedcharge.de",     "ev",        "Cologne",      None,275, 15,  "2024-08-01", "suspended", "speedcharge-ev"),
    ("Sara Klein",          "s.klein@speedcharge.de",       "ev",        "Hamburg",      27,  340, 27,  "2024-04-15", "active",    "speedcharge-ev"),
    ("Dominik Fischer",     "d.fischer@speedcharge.de",     "ev",        "Munich",       None,315, None,"2024-07-22", "active",    "speedcharge-ev"),
    ("Alicia Krause",       "a.krause@speedcharge.de",      "ev",        "Düsseldorf",   25,  360,  1,  "2025-01-30", "active",    "speedcharge-ev"),
    ("Marco Becker",        "m.becker@speedcharge.de",      "ev",        "Nuremberg",    28,  285,  8,  "2024-10-05", "active",    "speedcharge-ev"),
    ("Vanessa Richter",     "v.richter@speedcharge.de",     "ev",        "Leipzig",      None,395, 22,  "2024-03-18", "cancelled", "speedcharge-ev"),
]

partner_lookup = {p.slug: p for p in partners}

customers = []
for row in customers_raw:
    name, email, device, city, salary_day, annual_saving, monthly_kwh, contract_start_str, status, slug = row
    p = partner_lookup[slug]
    c = Customer(
        partner_id=p.id,
        name=name,
        email=email,
        device_type=device,
        city=city,
        tariff_type="dynamic",
        monthly_kwh=Decimal(str(monthly_kwh)) if monthly_kwh else None,
        annual_saving_eur=Decimal(str(annual_saving)),
        salary_day=salary_day,
        contract_start=date.fromisoformat(contract_start_str),
        contract_status=status,
    )
    db.add(c)
    db.flush()
    customers.append(c)

db.commit()

# ── Payments ───────────────────────────────────────────────────────────────────
random.seed(42)

AMOUNT_BY_DEVICE = {"heat_pump": (85, 145), "ev": (65, 120), "battery": (110, 180)}
FAILURE_REASONS = ["insufficient_funds", "expired_card", "bank_block", "sepa_reject", "unknown"]

def make_payments(customer: Customer):
    today = date.today()
    months_active = max(1, (today - customer.contract_start).days // 30)
    months_to_seed = min(months_active, 12)
    lo, hi = AMOUNT_BY_DEVICE[customer.device_type]

    payments = []
    for i in range(months_to_seed, 0, -1):
        period = (today.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        due = period.replace(day=customer.salary_day or 15)
        amount = Decimal(str(round(random.uniform(lo, hi), 2)))

        # Failure rates: cancelled/suspended = 60%, active = 25%
        fail_chance = 0.60 if customer.contract_status in ("suspended", "cancelled") else 0.25
        is_failed = random.random() < fail_chance

        if is_failed:
            reason = random.choice(FAILURE_REASONS)
            retry_count = random.randint(0, 3)
            status = "written_off" if retry_count >= 3 else ("retrying" if retry_count > 0 else "failed")
            p = Payment(
                customer_id=customer.id,
                amount_eur=amount,
                period_month=period,
                due_date=due,
                status=status,
                failure_reason=reason,
                failure_classified_by="manual",
                retry_count=retry_count,
                max_retries=3,
                next_retry_date=(due + timedelta(days=7)) if status == "retrying" else None,
            )
        else:
            paid_at = datetime.combine(due + timedelta(days=random.randint(0, 2)), datetime.min.time())
            p = Payment(
                customer_id=customer.id,
                amount_eur=amount,
                period_month=period,
                due_date=due,
                paid_at=paid_at,
                status="paid",
            )
        db.add(p)
        payments.append(p)

    db.flush()
    return payments


all_payments = []
for customer in customers:
    pmts = make_payments(customer)
    all_payments.extend(pmts)

db.commit()

# ── Churn Scores (heuristic) ───────────────────────────────────────────────────
for customer in customers:
    pmts = [p for p in all_payments if str(p.customer_id) == str(customer.id)]
    failed = sum(1 for p in pmts if p.status in ("failed", "retrying", "written_off"))
    total = len(pmts)
    contract_age = (date.today() - customer.contract_start).days

    score = 0
    if total > 0:
        score += int((failed / total) * 50)
    if contract_age < 60:
        score += 15
    if customer.contract_status == "suspended":
        score += 25
    elif customer.contract_status == "cancelled":
        score = 95
    score = min(score, 100)

    if score <= 25:
        risk = "low"
    elif score <= 50:
        risk = "medium"
    elif score <= 75:
        risk = "high"
    else:
        risk = "critical"

    cs = ChurnScore(
        customer_id=customer.id,
        score=score,
        risk_level=risk,
        reasoning=f"Heuristic seed: {failed}/{total} failed payments, contract age {contract_age}d.",
        factors={
            "failed_payments_30d": failed,
            "contract_age_days": contract_age,
            "device_type": customer.device_type,
            "is_dynamic_tariff": True,
        },
        action_suggested=(
            "Immediate outreach required" if risk == "critical"
            else "Schedule retention call" if risk == "high"
            else "Monitor" if risk == "medium"
            else "No action needed"
        ),
    )
    db.add(cs)

db.commit()

failed_q = sum(1 for p in all_payments if p.status in ("failed", "retrying"))
print(f"✓ Seeded {len(partners)} partners, {len(customers)} customers, {len(all_payments)} payments ({failed_q} failed/retrying in queue).")

db.close()
