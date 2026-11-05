# Lab 6 — Code and Branch Coverage

## Objective
Add pytest tests for `cloud_storage_tier.py` and achieve high line and branch coverage.

## Files
- `cloud_storage_tier.py` — original module provided in the lab repository (unchanged).
- `test_cloud_storage.py` — completed test suite.

## Run the tests
Open a terminal in this folder and run:

```bash
python -m pip install pytest pytest-cov
python -m pytest -v
python -m pytest --cov=cloud_storage_tier --cov-branch --cov-report=term-missing
```

## Verified result
- 20 tests passed.
- Line coverage: 100%.
- Branch coverage: 100%.

The tests cover input validation, inactive tenants, all storage tiers, invalid tiers and bucket sizes, corrupted buckets, large-bucket discounts, egress overage, backup fees, audit status, zero usage, and replication-latency monitoring.

Lab 7 and Lab 12 are not included or modified.
