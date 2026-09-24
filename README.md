# ACME Healthcare Data Project

This is a small SQLite pipeline for the four ACME Healthcare source files. It loads the data, splits provider names, and writes the requested reports.

## Running it

From the project directory, run:

```powershell
python src/ingest.py
```

The script recreates `acme_claims.db` and writes the reports under `output/`.

The source files are:

`acme_data_enrollment.txt`
`acme_data_medical_claims.txt`
`acme_data_pharmacy_claims.txt`
`acme_data_providers.txt`

The files are not all in the same format: enrollment, medical claims, and providers are pipe-delimited, while pharmacy claims are comma-delimited. The loader also ignores the row-count and completion-time lines appended to the medical claims export.

## Assumptions

The latest enrollment snapshot is used when a member appears more than once.
A non-null end date other than `3000/01/01` marks a member as disenrolled.
Provider names are parsed as first name, optional middle initial, and last name. Names with more than one word in the last-name portion are kept together.
`NULL` values are stored as missing values.
Claim spend is based on `allowed_amount`.

## Reports

`output/member_report.csv` contains one row per member, PCP details, disenrollment status, spend, and claim counts.
`output/claims_99214_3074F.csv` contains claims with `99214` on one line and `3074F` on another line.
`output/orphan_medical_claims.csv` contains medical claims whose member is not present in enrollment.
`output/run_timestamp.txt` records when the pipeline last ran.

## SQL files

The `sql/` directory contains the table definitions and the queries used for the reports. The Python script is the runnable pipeline; the SQL files are included to show the individual steps.

## Debugging the orphan-member query

The original query was:

```sql
SELECT *
FROM dbo.medical_claims mc
WHERE NOT EXISTS (
    SELECT member_id
    FROM dbo.eligibility e
)
```

The `NOT EXISTS` subquery is not connected to the outer medical-claims query. It checks whether the enrollment table contains any rows, but it never compares the current claim's `member_id` with `eligibility.member_id`.

If `dbo.eligibility` has at least one row, the subquery is true for every claim, so `NOT EXISTS` is false for every claim. If the table is empty, every medical claim is returned. The selected column inside `EXISTS` is not the problem; `EXISTS` only checks whether a row is returned.

The corrected correlated query is:

```sql
SELECT mc.*
FROM dbo.medical_claims AS mc
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.eligibility AS e
    WHERE e.member_id = mc.member_id
);
```

The important part is `WHERE e.member_id = mc.member_id`. It checks each medical claim against the enrollment table separately.

An equivalent `LEFT JOIN` solution is:

```sql
SELECT mc.*
FROM dbo.medical_claims AS mc
LEFT JOIN dbo.eligibility AS e
    ON e.member_id = mc.member_id
WHERE e.member_id IS NULL;
```

The `LEFT JOIN` keeps every medical claim. When no enrollment row matches, the enrollment columns are `NULL`, so the final condition identifies the orphan claims.

This project uses SQLite, where the equivalent table names are `medical_claims` and `enrollment` without the `dbo` schema prefix:

```sql
SELECT mc.*
FROM medical_claims AS mc
LEFT JOIN enrollment AS e
    ON e.member_id = mc.member_id
WHERE e.member_id IS NULL;
```
