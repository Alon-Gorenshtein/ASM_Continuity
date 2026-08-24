import json
import pandas as pd
from lib.config import INTERMEDIATE, TABLES, PROJECT_ROOT


def main():
    epilepsy = pd.read_parquet(INTERMEDIATE / "epilepsy_admissions.parquet")
    transitions = pd.read_parquet(INTERMEDIATE / "icu_floor_transitions.parquet")
    eligible = pd.read_parquet(INTERMEDIATE / "eligible_transitions.parquet")
    analysis = pd.read_parquet(INTERMEDIATE / "analysis_dataset.parquet")
    gaps = pd.read_parquet(INTERMEDIATE / "gaps_threshold_1.5.parquet")

    with open(TABLES / "descriptive_and_logistic.json") as f:
        descriptive_and_logistic = json.load(f)
    with open(TABLES / "iv_oral_and_sensitivity.json") as f:
        iv_oral_and_sensitivity = json.load(f)
    with open(TABLES / "demographic_descriptive.json") as f:
        demographic_descriptive = json.load(f)
    with open(TABLES / "transfer_vs_control.json") as f:
        transfer_vs_control = json.load(f)
    with open(TABLES / "delay_duration.json") as f:
        delay_duration = json.load(f)
    active_orders = pd.read_parquet(INTERMEDIATE / "active_asm_at_transition.parquet")

    cohort_flow = {
        "epilepsy_admissions": len(epilepsy),
        "epilepsy_subjects": int(epilepsy["subject_id"].nunique()),
        "status_epilepticus_admissions": int(epilepsy["status_epilepticus"].sum()),
        "icu_to_floor_transitions": len(transitions),
        "eligible_transitions": len(eligible),
        "eligible_admissions": int(eligible["hadm_id"].nunique()),
        "drug_observations_before_dose_confirmation": len(active_orders),
        "not_evaluable_count": int((~gaps["evaluable"]).sum()),
        "analysis_dataset_rows": len(analysis),
        "analysis_dataset_admissions": int(analysis["hadm_id"].nunique()),
        "analysis_dataset_subjects": int(analysis["subject_id"].nunique()),
    }
    results_digest = {
        "cohort_flow": cohort_flow,
        "headline": {
            "gap_rate": descriptive_and_logistic["overall"]["rate"],
            "gap_rate_ci": [descriptive_and_logistic["overall"]["ci_low"],
                             descriptive_and_logistic["overall"]["ci_high"]],
            "n_gap": descriptive_and_logistic["overall"]["n_gap"],
            "n": descriptive_and_logistic["overall"]["n"],
            "comparator_pre_control_p": transfer_vs_control["pre_control"]["mcnemar_p"],
            "comparator_post_control_p": transfer_vs_control["post_control"]["mcnemar_p"],
            "comparator_pre_rate_diff": transfer_vs_control["pre_control"]["rate_diff"],
            "comparator_post_rate_diff": transfer_vs_control["post_control"]["rate_diff"],
        },
    }
    stats_digest = {
        "descriptive_and_logistic": descriptive_and_logistic,
        "iv_oral_and_sensitivity": iv_oral_and_sensitivity,
        "demographic_descriptive": demographic_descriptive,
        "transfer_vs_control": transfer_vs_control,
        "delay_duration": delay_duration,
    }

    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "results_digest.json", "w") as f:
        json.dump(results_digest, f, indent=2, default=str)
    with open(output_dir / "stats_digest.json", "w") as f:
        json.dump(stats_digest, f, indent=2, default=str)
    print("Wrote results_digest.json and stats_digest.json")
    print(json.dumps(cohort_flow, indent=2))


if __name__ == "__main__":
    main()
