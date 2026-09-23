CREATE TABLE IF NOT EXISTS providers (
    provider_id TEXT,
    provider_npi_number TEXT,
    provider_name TEXT,
    provider_first_name TEXT,
    provider_middle_initial TEXT,
    provider_last_name TEXT,
    supplier_name TEXT
);

CREATE TABLE IF NOT EXISTS enrollment (
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
);

CREATE TABLE IF NOT EXISTS medical_claims (
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
);

CREATE TABLE IF NOT EXISTS pharmacy_claims (
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
);

CREATE INDEX IF NOT EXISTS idx_medical_member ON medical_claims(member_id);
CREATE INDEX IF NOT EXISTS idx_pharmacy_member ON pharmacy_claims(member_id);
CREATE INDEX IF NOT EXISTS idx_enrollment_member ON enrollment(member_id);
