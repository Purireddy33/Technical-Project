import csv
from datetime import datetime
import re
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "acme_claims.db"
OUTPUT_DIR = BASE_DIR / "output"


def normalize_value(value):
    if value is None:
        return None
    text = str(value).strip()
    if text.upper() == "NULL":
        return None
    return text


def split_provider_name(full_name):
    cleaned = normalize_value(full_name)
    result = {
        "provider_first_name": None,
        "provider_middle_initial": None,
        "provider_last_name": None,
    }

    if not cleaned:
        return result

    cleaned = re.sub(r"\s+", " ", cleaned).replace(".", " ")
    tokens = [token for token in cleaned.split() if token]
    if not tokens:
        return result

    common_suffixes = {"MD", "DO", "DPM", "DDS", "PA", "JR", "SR", "II", "III"}
    if tokens[-1].upper() in common_suffixes:
        tokens = tokens[:-1]

    if not tokens:
        return result

    first = tokens[0]
    result["provider_first_name"] = first

    if len(tokens) == 1:
        return result

    if len(tokens) == 2:
        result["provider_last_name"] = tokens[1]
        return result

    second = tokens[1]
    if len(second) <= 2 and second.upper() not in {"AND", "OF", "THE"}:
        result["provider_middle_initial"] = second
        result["provider_last_name"] = " ".join(tokens[2:])
    else:
        result["provider_last_name"] = " ".join(tokens[1:])

    return result


def read_delimited_file(file_path: Path, delimiter: str):
    with file_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        rows = []
        for row in reader:
            if not row or None in row:
                continue
            if any(
                str(value or "").strip().startswith(("(", "Completion time:"))
                for value in row.values()
            ):
                continue
            rows.append({key.lstrip("\ufeff"): normalize_value(value) for key, value in row.items()})
        return rows


def build_database():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("DROP TABLE IF EXISTS medical_claims")
    cursor.execute("DROP TABLE IF EXISTS pharmacy_claims")
    cursor.execute("DROP TABLE IF EXISTS enrollment")
    cursor.execute("DROP TABLE IF EXISTS providers")

    cursor.execute(
        """
        CREATE TABLE providers (
            provider_id TEXT,
            provider_npi_number TEXT,
            provider_name TEXT,
            provider_first_name TEXT,
            provider_middle_initial TEXT,
            provider_last_name TEXT,
            supplier_name TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE enrollment (
            member_id INTEGER,
            member_first_name TEXT,
            member_last_name TEXT,
            date_of_birth TEXT,
            date_of_death TEXT,
            gender TEXT,
            eligibility_snapshot_month TEXT,
            effdate TEXT,
            enddate TEXT,
            plan_code TEXT,
            pcp_id TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE medical_claims (
            claim_id INTEGER,
            member_id INTEGER,
            line_number INTEGER,
            claim_type_code TEXT,
            charge_submitted REAL,
            allowed_amount REAL,
            co_insurance REAL,
            copayment REAL,
            deductible REAL,
            provider_id TEXT,
            date_of_first_service TEXT,
            date_of_last_service TEXT,
            procedure_code TEXT,
            procedure_modifier_code_1 TEXT,
            place_of_service_code TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE pharmacy_claims (
            claim_id INTEGER,
            member_id INTEGER,
            allowed_amount REAL,
            co_insurance REAL,
            copayment REAL,
            deductible REAL,
            rx_refill_number INTEGER,
            date_of_service TEXT,
            date_paid TEXT,
            dispensing_provider_id TEXT
        )
        """
    )

    provider_rows = read_delimited_file(BASE_DIR / "acme_data_providers.txt", "|")
    provider_values = []
    for row in provider_rows:
        parsed_name = split_provider_name(row.get("PROVIDER_NAME"))
        provider_values.append(
            (
                row.get("PROVIDER_ID"),
                row.get("PROVIDER_NPI_NUMBER"),
                row.get("PROVIDER_NAME"),
                parsed_name["provider_first_name"],
                parsed_name["provider_middle_initial"],
                parsed_name["provider_last_name"],
                row.get("SUPPLIER_NAME"),
            )
        )
    cursor.executemany(
        """
        INSERT INTO providers (
            provider_id,
            provider_npi_number,
            provider_name,
            provider_first_name,
            provider_middle_initial,
            provider_last_name,
            supplier_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        provider_values,
    )

    enrollment_rows = read_delimited_file(BASE_DIR / "acme_data_enrollment.txt", "|")
    enrollment_values = [
        (
            row.get("MEMBER_ID"),
            row.get("MEMBER_FIRST_NAME"),
            row.get("MEMBER_LAST_NAME"),
            row.get("DATE_OF_BIRTH"),
            row.get("DATE_OF_DEATH"),
            row.get("GENDER"),
            row.get("ELIGIBILITY_SNAPSHOT_MONTH"),
            row.get("EFFDATE"),
            row.get("ENDDATE"),
            row.get("PLAN_CODE"),
            row.get("PCP_ID"),
        )
        for row in enrollment_rows
    ]
    cursor.executemany(
        """
        INSERT INTO enrollment (
            member_id,
            member_first_name,
            member_last_name,
            date_of_birth,
            date_of_death,
            gender,
            eligibility_snapshot_month,
            effdate,
            enddate,
            plan_code,
            pcp_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        enrollment_values,
    )

    medical_rows = read_delimited_file(BASE_DIR / "acme_data_medical_claims.txt", "|")
    medical_values = [
        (
            row.get("CLAIM_ID"),
            row.get("member_id"),
            row.get("LINE_NUMBER"),
            row.get("CLAIM_TYPE_CODE"),
            row.get("CHARGE_SUBMITTED"),
            row.get("ALLOWED_AMOUNT"),
            row.get("CO_INSURANCE"),
            row.get("COPAYMENT"),
            row.get("DEDUCTIBLE"),
            row.get("PROVIDER_ID"),
            row.get("DATE_OF_FIRST_SERVICE"),
            row.get("DATE_OF_LAST_SERVICE"),
            row.get("PROCEDURE_CODE"),
            row.get("PROCEDURE_MODIFIER_CODE_1"),
            row.get("PLACE_OF_SERVICE_CODE"),
        )
        for row in medical_rows
    ]
    cursor.executemany(
        """
        INSERT INTO medical_claims (
            claim_id,
            member_id,
            line_number,
            claim_type_code,
            charge_submitted,
            allowed_amount,
            co_insurance,
            copayment,
            deductible,
            provider_id,
            date_of_first_service,
            date_of_last_service,
            procedure_code,
            procedure_modifier_code_1,
            place_of_service_code
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        medical_values,
    )

    pharmacy_rows = read_delimited_file(BASE_DIR / "acme_data_pharmacy_claims.txt", ",")
    pharmacy_values = [
        (
            row.get("CLAIM_ID"),
            row.get("MEMBER_ID"),
            row.get("ALLOWED_AMOUNT"),
            row.get("CO_INSURANCE"),
            row.get("COPAYMENT"),
            row.get("DEDUCTIBLE"),
            row.get("RX_REFILL_NUMBER"),
            row.get("DATE_OF_SERVICE"),
            row.get("DATE_PAID"),
            row.get("DISPENSING_PROVIDER_ID"),
        )
        for row in pharmacy_rows
    ]
    cursor.executemany(
        """
        INSERT INTO pharmacy_claims (
            claim_id,
            member_id,
            allowed_amount,
            co_insurance,
            copayment,
            deductible,
            rx_refill_number,
            date_of_service,
            date_paid,
            dispensing_provider_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        pharmacy_values,
    )

    cursor.executescript(
        """
        CREATE INDEX idx_providers_provider_id ON providers(provider_id);
        CREATE INDEX idx_enrollment_member_id ON enrollment(member_id);
        CREATE INDEX idx_enrollment_pcp_id ON enrollment(pcp_id);
        CREATE INDEX idx_medical_member_id ON medical_claims(member_id);
        CREATE INDEX idx_medical_claim_id ON medical_claims(claim_id);
        CREATE INDEX idx_medical_procedure ON medical_claims(procedure_code);
        CREATE INDEX idx_pharmacy_member_id ON pharmacy_claims(member_id);
        """
    )

    connection.commit()
    connection.close()


def export_reports():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    run_time = datetime.now().astimezone().isoformat(timespec="seconds")
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    member_report_query = """
        WITH latest_enrollment AS (
             SELECT member_id,
                 member_first_name,
                 member_last_name,
                 pcp_id,
                 enddate,
                 eligibility_snapshot_month,
                 effdate,
                   ROW_NUMBER() OVER (
                       PARTITION BY member_id
                       ORDER BY eligibility_snapshot_month DESC, effdate DESC, enddate DESC
                   ) AS row_number
            FROM enrollment
        ),
        provider_lookup AS (
            SELECT provider_id, provider_first_name, provider_last_name
            FROM (
                SELECT provider_id,
                       provider_first_name,
                       provider_last_name,
                       ROW_NUMBER() OVER (
                           PARTITION BY provider_id
                           ORDER BY provider_npi_number, provider_name
                       ) AS row_number
                FROM providers
            )
            WHERE row_number = 1
        ),
        med AS (
            SELECT member_id,
                   SUM(COALESCE(allowed_amount, 0)) AS medical_spend,
                   COUNT(DISTINCT claim_id) AS medical_claim_count
            FROM medical_claims
            GROUP BY member_id
        ),
        pharm AS (
            SELECT member_id,
                   SUM(COALESCE(allowed_amount, 0)) AS pharmacy_spend,
                   COUNT(DISTINCT claim_id) AS pharmacy_claim_count
            FROM pharmacy_claims
            GROUP BY member_id
        )
        SELECT
            e.member_id,
            e.member_first_name,
            e.member_last_name,
            e.pcp_id,
            p.provider_first_name AS pcp_first_name,
            p.provider_last_name AS pcp_last_name,
            CASE
                WHEN e.enddate IS NOT NULL AND e.enddate NOT IN ('NULL', '3000/01/01') THEN 'Y'
                ELSE 'N'
            END AS disenrolled,
            COALESCE(m.medical_spend, 0) AS medical_claims_spend,
            COALESCE(ph.pharmacy_spend, 0) AS pharmacy_claim_spend,
            COALESCE(m.medical_claim_count, 0) AS medical_claim_count,
            COALESCE(ph.pharmacy_claim_count, 0) AS pharmacy_claim_count
        FROM latest_enrollment e
        LEFT JOIN med m ON m.member_id = e.member_id
        LEFT JOIN pharm ph ON ph.member_id = e.member_id
        LEFT JOIN provider_lookup p ON p.provider_id = e.pcp_id
        WHERE e.row_number = 1
        ORDER BY e.member_id
    """

    claims_query = """
        SELECT DISTINCT m1.member_id,
               m1.claim_id,
               m1.provider_id,
               m1.date_of_first_service,
               m1.procedure_code,
               m2.procedure_code AS second_procedure_code
        FROM medical_claims m1
        JOIN medical_claims m2
          ON m1.claim_id = m2.claim_id
                 AND m1.line_number <> m2.line_number
        WHERE m1.procedure_code = '99214'
          AND m2.procedure_code = '3074F'
        ORDER BY m1.claim_id
    """

    orphan_query = """
        SELECT mc.member_id,
               mc.claim_id,
               mc.provider_id,
               mc.date_of_first_service,
               mc.procedure_code,
               mc.allowed_amount
        FROM medical_claims mc
        LEFT JOIN enrollment e
          ON e.member_id = mc.member_id
        WHERE e.member_id IS NULL
        ORDER BY mc.claim_id
    """

    for file_name, query in {
        "member_report.csv": member_report_query,
        "claims_99214_3074F.csv": claims_query,
        "orphan_medical_claims.csv": orphan_query,
    }.items():
        rows = connection.execute(query).fetchall()
        with (OUTPUT_DIR / file_name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            if rows:
                writer.writerow(rows[0].keys())
                for row in rows:
                    writer.writerow([row[col] for col in row.keys()])
            else:
                writer.writerow([])

    (OUTPUT_DIR / "run_timestamp.txt").write_text(run_time + "\n", encoding="utf-8")
    connection.close()
    print(f"Run completed at: {run_time}")
    print(f"SQLite database refreshed at: {DB_PATH}")
    print(f"Reports exported to: {OUTPUT_DIR}")


if __name__ == "__main__":
    build_database()
    export_reports()
