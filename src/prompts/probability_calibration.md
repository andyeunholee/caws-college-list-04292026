# Profile-Adjusted Acceptance Probability — Calibration Rubric

You must output a **profile-adjusted estimated acceptance probability** for each college, NOT the raw published acceptance rate. Your goal is to give a realistic decision-making number for THIS specific student at THIS specific college.

## Step-by-step calibration

For each college, start from the raw overall acceptance rate (or, when available, the early-round rate if the student is applying early), then apply these multiplicative factors:

### 1. Academic fit vs. the school's 25th-75th SAT/GPA band
- Student's stats above the 75th percentile band → multiply by 1.4-1.8
- In the 50th-75th band → multiply by 1.1-1.3
- In the 25th-50th band → multiply by 0.7-0.9
- Below the 25th band → multiply by 0.3-0.5

### 2. Selectivity of intended major
- Pre-Med / BS-MD / direct-admit nursing / engineering at top schools: multiply by 0.5-0.8
- Business at Wharton/Stern/Ross/McIntire: multiply by 0.5-0.7
- Standard liberal arts major: multiply by 1.0
- Less competitive major at the same school: multiply by 1.1-1.2

### 3. Hooks
- Recruited athlete with coach support: multiply by 3-8 (capped at 0.95)
- Legacy at a school that meaningfully considers it (Penn, Notre Dame, etc.): multiply by 1.3-1.7
- Underrepresented minority / first-gen at holistic schools: multiply by 1.1-1.4
- QuestBridge Match Finalist for a partner school: floor at 0.30 if matched-rank, else 1.2-1.5
- Strong demonstrated interest at schools that track it (BU, Tulane, Northeastern, Lehigh): multiply by 1.2-1.4

### 4. Round bonus (when applicable)
- ED at a school that gives a meaningful ED boost (Penn, Duke, Northwestern, Vanderbilt, WashU, JHU, Cornell, etc.): multiply by 1.5-2.5
- REA/SCEA: very small boost (1.05-1.15) — those schools aim to keep ED-equivalent yield low.
- EA at non-restrictive schools: usually no meaningful boost (1.0-1.05).

### 5. Floor and ceiling
- Final probability must be in [0.01, 0.95]
- Round to two decimals (e.g., 0.18, 0.42, 0.83)

## Tier definitions (based on the FINAL adjusted probability)
- **Reach**: adjusted probability < 0.25
- **Match**: 0.25 ≤ adjusted probability < 0.60
- **Safety**: adjusted probability ≥ 0.60

The same college can be a Reach for one student and a Match for another. Place the college in the tier that matches its FINAL adjusted probability for THIS student.

## Worked example

Student: 1450 SAT, 3.95 UW GPA, AP rigor 9 courses, strong ECs, Pre-Med, no major hooks, applying RD.
- **Cornell University**: raw RD admit ≈ 7%. Stats slightly above the 25th-75th band → ×1.3. Pre-Med at Cornell (CALS bio path) is moderately selective → ×0.85. No hooks → ×1.0. RD round → ×1.0. → 0.07 × 1.3 × 0.85 = **0.077** ≈ 0.08. Reach.
- **University of Michigan (out-of-state)**: raw OOS rate ≈ 18%. Stats above median → ×1.3. Pre-Med at LSA → ×0.9. No hooks → ×1.0. → 0.18 × 1.3 × 0.9 = **0.21**. Reach (just under 0.25 line).
- **Boston University**: raw rate ≈ 14%. Stats well above median → ×1.5. Standard major → ×1.0. Demonstrated interest matters at BU → ×1.25. → 0.14 × 1.5 × 1.25 = **0.26**. Match.

## Reasoning factor field
For each college, write a single short clause (≤ 12 words) explaining the dominant factor that moved your probability away from raw, e.g.:
- "stats above 75th band; Pre-Med selectivity offset"
- "ED boost applied; legacy not meaningfully considered"
- "recruited athlete probability floor"
- "in-state public; high stats; near guaranteed merit"
