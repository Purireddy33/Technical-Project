-- The Python loader fills these columns when it reads the provider file.
SELECT
    provider_id,
    provider_name,
    provider_first_name,
    provider_middle_initial,
    provider_last_name,
    supplier_name
FROM providers;
