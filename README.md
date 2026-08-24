# Antiseizure Medication Administration Gaps Across the ICU-to-Floor Transfer: A Matched Within-Patient Comparison

Gorenshtein A, Adiniaev Y, Klang E, Daniel O. Department of Neurology and BRIDGE GenAI Lab, Beth Israel Deaconess Medical Center, Harvard Medical School, Boston, MA, USA. Corresponding author: Alon Gorenshtein, MD (agorensh@bidmc.harvard.edu).

Repository: https://github.com/Alon-Gorenshtein/study_asm_continuity

Objective: Whether a scheduled antiseizure medication (ASM) continues on schedule across the ICU-to-floor transfer, a recognized point of vulnerability for medication errors, has not been characterized. We quantified ASM administration-gap frequency across this transfer and compared it with gap frequency during matched non-transfer intervals in the same patient and drug.

## Data

This study uses the **MIMIC-IV v3.1** database, available to credentialed users from PhysioNet:

https://physionet.org/content/mimiciv/3.1/

Raw data are **not** included in this repository and cannot be redistributed under the PhysioNet data use agreement. Obtain credentialed access, download the dataset, and set the local data path in `code/config.py` (replace the `/path/to/mimic-iv-3.1` placeholder). 

## Reproducing the analysis

1. Clone this repository: `git clone https://github.com/Alon-Gorenshtein/study_asm_continuity.git`
2. Use Python 3.9 or later. Install the scientific stack: `pandas numpy scipy scikit-learn statsmodels` (and `lifelines`, `torch` where the scripts require them).
2. Point the data-path variable at the top of `code/config.py` to your local copy of MIMIC-IV.
3. Run the scripts in `code/` in numeric order (`00_*`, `01_*`, ...). Intermediate and final outputs are written to `./output/`.

## Repository contents

- `code/` — the full analysis pipeline (cohort construction, extraction, statistics, and figures). Local file-system paths have been replaced with `/path/to/...` placeholders.
- a BibTeX/AMA reference file is included.

## Citation

Gorenshtein A, Adiniaev Y, Klang E, Daniel O. Antiseizure Medication Administration Gaps Across the ICU-to-Floor Transfer: A Matched Within-Patient Comparison. 2026.

## License

The code is released under an open-source license on publication.
