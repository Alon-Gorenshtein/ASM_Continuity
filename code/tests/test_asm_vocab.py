from lib.asm_vocab import (
    canonical_drug, route_class, is_alcohol_withdrawal_order, expected_interval_hours,
)


def test_canonical_drug_merges_fosphenytoin_into_phenytoin():
    assert canonical_drug("Fosphenytoin") == "phenytoin"
    assert canonical_drug("Phenytoin Sodium Extended") == "phenytoin"
    assert canonical_drug("Phenytoin Infatab") == "phenytoin"


def test_canonical_drug_merges_valproate_variants():
    assert canonical_drug("Divalproex (Extended Release)") == "valproate"
    assert canonical_drug("Divalproex (Delayed Release)") == "valproate"
    assert canonical_drug("Valproate Sodium") == "valproate"


def test_canonical_drug_case_insensitive_and_unknown():
    assert canonical_drug("LeVETiracetam") == "levetiracetam"
    assert canonical_drug("Heparin") is None
    assert canonical_drug(None) is None


def test_route_class():
    assert route_class("levetiracetam") == "iv_available"
    assert route_class("lamotrigine") == "oral_only"
    assert route_class("ibuprofen") == "unknown"


def test_is_alcohol_withdrawal_order():
    assert is_alcohol_withdrawal_order(
        "Phenobarbital Alcohol Withdrawal Dose Taper (Days 2-7)"
    ) is True
    assert is_alcohol_withdrawal_order("Phenobarbital") is False


def test_expected_interval_hours():
    assert expected_interval_hours(2) == 12.0
    assert expected_interval_hours("2") == 12.0
    assert expected_interval_hours(0) is None
    assert expected_interval_hours(None) is None
    assert expected_interval_hours("") is None


def test_non_scheduled_pattern_matches_prn_and_once():
    from lib.asm_vocab import NON_SCHEDULED_PATTERN
    assert NON_SCHEDULED_PATTERN.search("PRN") is not None
    assert NON_SCHEDULED_PATTERN.search("ONCE") is not None
    assert NON_SCHEDULED_PATTERN.search("BID") is None
    assert NON_SCHEDULED_PATTERN.search("Q12H") is None
