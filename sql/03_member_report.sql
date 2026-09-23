WITH latest_enrollment AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY member_id
               ORDER BY eligibility_snapshot_month DESC, effdate DESC, enddate DESC
           ) AS row_number
    FROM enrollment
),
med AS (
    SELECT
        member_id,
        SUM(COALESCE(allowed_amount, 0)) AS medical_spend,
        COUNT(DISTINCT claim_id) AS medical_claim_count
    FROM medical_claims
    GROUP BY member_id
),
pharm AS (
    SELECT
        member_id,
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
LEFT JOIN providers p ON p.provider_id = e.pcp_id
WHERE e.row_number = 1
ORDER BY e.member_id;
