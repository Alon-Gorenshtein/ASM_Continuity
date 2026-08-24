"""Canonical antiseizure-medication (ASM) vocabulary shared by every extraction/analysis script.

Fosphenytoin is merged into "phenytoin": it is a prodrug of phenytoin (the active moiety is
identical), and IV fosphenytoin -> oral phenytoin is a routine formulation change during an
ICU-to-floor transition, not a change of drug -- counting it as a "switch" would misclassify the most
common legitimate substitution in this cohort as a gap-masking event.
"""
import re

ASM_NAME_PATTERN = re.compile(
    r"levetiracetam|phenytoin|fosphenytoin|valproate|divalproex|lacosamide|"
    r"phenobarbital|oxcarbazepine|lamotrigine|topiramate|zonisamide|carbamazepine",
    re.IGNORECASE,
)
NON_SCHEDULED_PATTERN = re.compile(r"\bPRN\b|\bONCE\b", re.IGNORECASE)
ALCOHOL_WITHDRAWAL_PATTERN = re.compile(r"alcohol withdrawal", re.IGNORECASE)

IV_AVAILABLE_DRUGS = {"levetiracetam", "phenytoin", "valproate", "phenobarbital", "lacosamide"}
ORAL_ONLY_DRUGS = {"lamotrigine", "topiramate", "zonisamide", "oxcarbazepine", "carbamazepine"}

ADMINISTERED_EVENT_TXT = {"Administered", "Delayed Administered", "Administered Bolus from IV Drip"}


def canonical_drug(medication):
    if not isinstance(medication, str):
        return None
    m = medication.lower()
    if "fosphenytoin" in m or "phenytoin" in m:
        return "phenytoin"
    if "levetiracetam" in m:
        return "levetiracetam"
    if "valproate" in m or "divalproex" in m:
        return "valproate"
    if "lacosamide" in m:
        return "lacosamide"
    if "phenobarbital" in m:
        return "phenobarbital"
    if "oxcarbazepine" in m:
        return "oxcarbazepine"
    if "lamotrigine" in m:
        return "lamotrigine"
    if "topiramate" in m:
        return "topiramate"
    if "zonisamide" in m:
        return "zonisamide"
    if "carbamazepine" in m:
        return "carbamazepine"
    return None


def route_class(canonical):
    if canonical in IV_AVAILABLE_DRUGS:
        return "iv_available"
    if canonical in ORAL_ONLY_DRUGS:
        return "oral_only"
    return "unknown"


def is_alcohol_withdrawal_order(medication):
    return bool(ALCOHOL_WITHDRAWAL_PATTERN.search(medication or ""))


def expected_interval_hours(doses_per_24_hrs):
    try:
        d = float(doses_per_24_hrs)
    except (TypeError, ValueError):
        return None
    if d <= 0:
        return None
    return 24.0 / d
