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

The subquery is not connected to `mc`. It only asks whether the eligibility table has any rows. It needs to compare the current claim's member to the enrollment table:

```sql
SELECT mc.*
FROM medical_claims mc
LEFT JOIN enrollment e
    ON e.member_id = mc.member_id
WHERE e.member_id IS NULL;
```
