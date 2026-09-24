SELECT DISTINCT
    m1.member_id,
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
ORDER BY m1.claim_id;
