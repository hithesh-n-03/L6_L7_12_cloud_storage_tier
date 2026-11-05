import pytest
from cloud_storage_tier import process_storage_tenants, monitor_replication_latency


def test_single_active_hot_tenant():
    tenants = [{
        "account_active": True, "tier": "hot", "has_backup_vault": False,
        "buckets": [{"size_gb": 100, "corrupted": False, "egress_gb": 50}]
    }]
    assert process_storage_tenants(tenants, 10.0) == {
        "total_billed": 2.5, "status": "BILLED"
    }


def test_invalid_tenant_argument():
    with pytest.raises(ValueError):
        process_storage_tenants("not a list", 10)


def test_negative_support_fee():
    with pytest.raises(ValueError):
        process_storage_tenants([], -1)


def test_inactive_tenant_is_skipped_and_zero_usage_returned():
    assert process_storage_tenants([{"account_active": False}], 10) == {
        "total_billed": 0.0, "status": "ZERO_USAGE"
    }


@pytest.mark.parametrize("tier,rate", [("hot", 0.025), ("cool", 0.015), ("archive", 0.005)])
def test_storage_tier_rates(tier, rate):
    result = process_storage_tenants([{
        "account_active": True, "tier": tier,
        "buckets": [{"size_gb": 100, "egress_gb": 0}]
    }], 10)
    assert result == {"total_billed": round(100 * rate, 2), "status": "BILLED"}


def test_unknown_tier_is_flagged():
    result = process_storage_tenants([{
        "account_active": True, "tier": "premium",
        "buckets": [{"size_gb": 100}]
    }], 10)
    assert result == {"total_billed": 0.0, "status": "ZERO_USAGE"}


def test_invalid_size_is_flagged_and_skipped():
    result = process_storage_tenants([{
        "account_active": True, "tier": "hot",
        "buckets": [{"size_gb": 0}, {"size_gb": -5}]
    }], 10)
    assert result == {"total_billed": 0.0, "status": "ZERO_USAGE"}


def test_corrupted_hot_bucket_is_flagged_but_not_charged():
    result = process_storage_tenants([{
        "account_active": True, "tier": "hot",
        "buckets": [{"size_gb": 100, "corrupted": True, "egress_gb": 0}]
    }], 10)
    assert result == {"total_billed": 0.0, "status": "ZERO_USAGE"}


def test_corrupted_archive_bucket_zeros_tenant_charge():
    result = process_storage_tenants([{
        "account_active": True, "tier": "archive", "has_backup_vault": True,
        "buckets": [
            {"size_gb": 100, "corrupted": False, "egress_gb": 0},
            {"size_gb": 20, "corrupted": True, "egress_gb": 0}
        ]
    }], 10)
    # Archive corruption breaks the bucket loop; backup fee is still added.
    assert result == {"total_billed": 10.0, "status": "BILLED"}


def test_large_bucket_discount_and_egress_overage():
    result = process_storage_tenants([{
        "account_active": True, "tier": "hot",
        "buckets": [{"size_gb": 600, "egress_gb": 150}]
    }], 10)
    expected = (600 * 0.025 * 0.90) + ((150 - 100) * 0.08)
    assert result == {"total_billed": round(expected, 2), "status": "BILLED"}


def test_small_bucket_and_egress_at_threshold():
    result = process_storage_tenants([{
        "account_active": True, "tier": "cool",
        "buckets": [{"size_gb": 500, "egress_gb": 100}]
    }], 10)
    assert result == {"total_billed": 7.5, "status": "BILLED"}


def test_backup_vault_fee_is_added():
    result = process_storage_tenants([{
        "account_active": True, "tier": "archive", "has_backup_vault": True,
        "buckets": []
    }], 10)
    assert result == {"total_billed": 10.0, "status": "BILLED"}


def test_audit_flag_when_flagged_count_exceeds_four():
    result = process_storage_tenants([{
        "account_active": True, "tier": "hot",
        "buckets": [{"size_gb": 0} for _ in range(5)]
    }], 10)
    assert result == {"total_billed": 0.0, "status": "AUDIT_FLAGGED"}


def test_audit_flag_from_invalid_tiers():
    tenants = [{"account_active": True, "tier": "unknown"} for _ in range(5)]
    result = process_storage_tenants(tenants, 10)
    assert result == {"total_billed": 0.0, "status": "AUDIT_FLAGGED"}


def test_monitor_replication_no_data():
    assert monitor_replication_latency([]) == "NO_DATA"


def test_monitor_replication_alert_after_two_consecutive_high_values():
    assert monitor_replication_latency([[100, 201, 250]]) == "SYNC_LAG_ALERT"


def test_monitor_replication_resets_streak_after_normal_latency():
    assert monitor_replication_latency([[201, 100, 201], [50, 200, 80]]) == "SYNCED"


def test_monitor_replication_synced_for_empty_node_logs():
    assert monitor_replication_latency([[], [100, 150, 200]]) == "SYNCED"
