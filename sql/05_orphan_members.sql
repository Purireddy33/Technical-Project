SELECT mc.*
FROM medical_claims mc
LEFT JOIN enrollment e
  ON e.member_id = mc.member_id
WHERE e.member_id IS NULL;
