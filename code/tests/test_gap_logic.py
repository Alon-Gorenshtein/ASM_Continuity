import pandas as pd
from lib.gap_logic import compute_gaps_for_threshold


def _base_frames():
    eligible = pd.DataFrame([
        {"stay_id": 1, "subject_id": 100, "hadm_id": 1000,
         "icu_outtime": pd.Timestamp("2180-01-01 12:00:00")},
        {"stay_id": 2, "subject_id": 200, "hadm_id": 2000,
         "icu_outtime": pd.Timestamp("2180-01-01 12:00:00")},
        {"stay_id": 3, "subject_id": 300, "hadm_id": 3000,
         "icu_outtime": pd.Timestamp("2180-01-01 12:00:00")},
    ])
    active_orders = pd.DataFrame([
        {"stay_id": 1, "canonical_drug": "levetiracetam", "expected_interval_hours": 12.0},
        {"stay_id": 2, "canonical_drug": "levetiracetam", "expected_interval_hours": 12.0},
        {"stay_id": 3, "canonical_drug": "levetiracetam", "expected_interval_hours": 12.0},
    ])
    dischtime_by_hadm = {1000: pd.Timestamp("2180-01-05"), 2000: pd.Timestamp("2180-01-05"),
                          3000: pd.Timestamp("2180-01-05")}
    return eligible, active_orders, dischtime_by_hadm


def test_on_time_dose_is_not_a_gap():
    eligible, active_orders, dischtime = _base_frames()
    emar = pd.DataFrame([
        {"subject_id": 100, "canonical_drug": "levetiracetam",
         "charttime": pd.Timestamp("2180-01-01 08:00:00")},
        {"subject_id": 100, "canonical_drug": "levetiracetam",
         "charttime": pd.Timestamp("2180-01-01 20:30:00")},
    ])
    out = compute_gaps_for_threshold(eligible[eligible.stay_id == 1], active_orders, emar, dischtime, 1.5)
    assert len(out) == 1
    assert out.iloc[0]["gap_flag"] == False
    assert out.iloc[0]["resumed_before_discharge"] == True


def test_delayed_dose_beyond_threshold_is_a_gap():
    eligible, active_orders, dischtime = _base_frames()
    emar = pd.DataFrame([
        {"subject_id": 200, "canonical_drug": "levetiracetam",
         "charttime": pd.Timestamp("2180-01-01 08:00:00")},
        {"subject_id": 200, "canonical_drug": "levetiracetam",
         "charttime": pd.Timestamp("2180-01-02 10:00:00")},  # 26h later, expected 12h
    ])
    out = compute_gaps_for_threshold(eligible[eligible.stay_id == 2], active_orders, emar, dischtime, 1.5)
    assert out.iloc[0]["gap_flag"] == True


def test_no_further_dose_before_discharge_is_a_gap():
    eligible, active_orders, dischtime = _base_frames()
    emar = pd.DataFrame([
        {"subject_id": 300, "canonical_drug": "levetiracetam",
         "charttime": pd.Timestamp("2180-01-01 08:00:00")},
    ])
    out = compute_gaps_for_threshold(eligible[eligible.stay_id == 3], active_orders, emar, dischtime, 1.5)
    assert out.iloc[0]["gap_flag"] == True
    assert out.iloc[0]["resumed_before_discharge"] == False


def test_same_day_switch_is_flagged_not_hidden():
    eligible, active_orders, dischtime = _base_frames()
    emar = pd.DataFrame([
        {"subject_id": 100, "canonical_drug": "levetiracetam",
         "charttime": pd.Timestamp("2180-01-01 08:00:00")},
        {"subject_id": 100, "canonical_drug": "phenytoin",
         "charttime": pd.Timestamp("2180-01-01 18:00:00")},
    ])
    out = compute_gaps_for_threshold(eligible[eligible.stay_id == 1], active_orders, emar, dischtime, 1.5)
    assert out.iloc[0]["same_day_switch"] == True


def test_no_confirmed_icu_dose_is_excluded_not_counted_as_gap():
    eligible, active_orders, dischtime = _base_frames()
    emar = pd.DataFrame([
        {"subject_id": 100, "canonical_drug": "levetiracetam",
         "charttime": pd.Timestamp("2180-01-01 14:00:00")},  # only AFTER icu_outtime, no ICU dose
    ])
    out = compute_gaps_for_threshold(eligible[eligible.stay_id == 1], active_orders, emar, dischtime, 1.5)
    assert len(out) == 0


def test_dose_from_different_hadm_id_is_not_a_confirmed_icu_dose():
    eligible, active_orders, dischtime = _base_frames()
    emar = pd.DataFrame([
        # subject 100's ACTUAL admission (hadm_id 1000) has no ASM dose before icu_outtime.
        # subject 100 also has a dose from a DIFFERENT hospitalization (hadm_id 9999) that happens
        # to be chronologically before icu_outtime -- this must NOT count as a confirmed ICU dose
        # for the hadm_id-1000 transition.
        {"subject_id": 100, "hadm_id": 9999, "canonical_drug": "levetiracetam",
         "charttime": pd.Timestamp("2175-06-01 08:00:00")},
        {"subject_id": 100, "hadm_id": 1000, "canonical_drug": "levetiracetam",
         "charttime": pd.Timestamp("2180-01-01 14:00:00")},  # only AFTER icu_outtime, this admission
    ])
    out = compute_gaps_for_threshold(eligible[eligible.stay_id == 1], active_orders, emar, dischtime, 1.5)
    assert len(out) == 0  # no confirmed same-admission ICU dose -> excluded, not a false gap or false non-gap


def test_no_further_dose_but_none_actually_due_before_discharge_is_not_evaluable():
    # Once-daily drug (expected_interval_hours=12 in these fixtures -- see _base_frames), last ICU
    # dose at 08:00, transfer at 12:00, discharge at 14:00 the SAME day. The next dose would not be
    # due until 20:00 -- after discharge -- so this is NOT a gap, it is not evaluable at all.
    eligible = pd.DataFrame([
        {"stay_id": 4, "subject_id": 400, "hadm_id": 4000,
         "icu_outtime": pd.Timestamp("2180-01-01 12:00:00")},
    ])
    active_orders = pd.DataFrame([
        {"stay_id": 4, "canonical_drug": "levetiracetam", "expected_interval_hours": 12.0},
    ])
    dischtime_by_hadm = {4000: pd.Timestamp("2180-01-01 14:00:00")}
    emar = pd.DataFrame([
        {"subject_id": 400, "canonical_drug": "levetiracetam",
         "charttime": pd.Timestamp("2180-01-01 08:00:00")},
    ])
    out = compute_gaps_for_threshold(eligible, active_orders, emar, dischtime_by_hadm, 1.5)
    assert len(out) == 1
    assert out.iloc[0]["evaluable"] == False
    assert out.iloc[0]["gap_flag"] == False


def test_no_further_dose_and_a_dose_was_due_before_discharge_stays_evaluable_and_a_gap():
    # Same setup, but discharge is 5 days later -- the next dose (due 20:00 the same day) was
    # clearly due and never given. Must remain evaluable=True, gap_flag=True (same as the existing
    # test_no_further_dose_before_discharge_is_a_gap, re-asserted here with the evaluable field).
    eligible = pd.DataFrame([
        {"stay_id": 3, "subject_id": 300, "hadm_id": 3000,
         "icu_outtime": pd.Timestamp("2180-01-01 12:00:00")},
    ])
    active_orders = pd.DataFrame([
        {"stay_id": 3, "canonical_drug": "levetiracetam", "expected_interval_hours": 12.0},
    ])
    dischtime_by_hadm = {3000: pd.Timestamp("2180-01-05")}
    emar = pd.DataFrame([
        {"subject_id": 300, "canonical_drug": "levetiracetam",
         "charttime": pd.Timestamp("2180-01-01 08:00:00")},
    ])
    out = compute_gaps_for_threshold(eligible, active_orders, emar, dischtime_by_hadm, 1.5)
    assert out.iloc[0]["evaluable"] == True
    assert out.iloc[0]["gap_flag"] == True
    assert out.iloc[0]["resumed_before_discharge"] == False
