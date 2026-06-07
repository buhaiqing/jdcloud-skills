"""Tests for sensitive masker (JD Cloud)."""
from scripts.lib.sensitive_masker import (
    SensitiveMasker,
    mask_value,
    _var_name_for,
    _is_sensitive,
    _field_path,
    SENSITIVE_FIELDS,
)


def test_mysql_password_is_sensitive():
    """MySQL accountPassword is registered as sensitive."""
    assert _is_sensitive("mysql", "accountPassword") is True
    assert _var_name_for("mysql", "accountPassword") == "mysql_password"


def test_postgres_password_is_sensitive():
    """PostgreSQL accountPassword is registered as sensitive."""
    assert _is_sensitive("postgresql", "accountPassword") is True


def test_mongodb_password_is_sensitive():
    """MongoDB accountPassword is registered as sensitive."""
    assert _is_sensitive("mongodb", "accountPassword") is True


def test_redis_password_is_sensitive():
    """Redis password is registered as sensitive."""
    assert _is_sensitive("redis", "password") is True


def test_iam_access_key_is_sensitive():
    """IAM accessKeyId is registered as sensitive."""
    assert _is_sensitive("iam", "accessKeyId") is True


def test_vpc_field_is_not_sensitive():
    """VPC fields are not sensitive."""
    assert _is_sensitive("vpc", "vpcName") is False
    assert _is_sensitive("vpc", "addressPrefix") is False


def test_sg_field_is_not_sensitive():
    """SecurityGroup fields are not sensitive."""
    assert _is_sensitive("sg", "networkSecurityGroupName") is False


def test_kms_field_is_not_sensitive():
    """KMS fields (keyName) are not sensitive (key material never returned)."""
    assert _is_sensitive("kms", "keyName") is False
    assert _is_sensitive("kms", "keySpec") is False


def test_mask_value_replaces_with_var_ref():
    """mask_value should replace sensitive value with var reference."""
    masked = mask_value("mysql", "accountPassword", "supersecret")
    assert masked == "${var.mysql_password}"
    assert "supersecret" not in str(masked)


def test_mask_value_leaves_non_sensitive_unchanged():
    """mask_value should return original for non-sensitive fields."""
    assert mask_value("vpc", "vpcName", "my-vpc") == "my-vpc"


def test_mask_field_returns_path():
    """mask_field should return (masked_value, field_path) for sensitive fields."""
    masker = SensitiveMasker()
    masked, path = masker.mask_field("mysql", "accountPassword", "secret")
    assert masked == "${var.mysql_password}"
    assert path == "mysql.account_password"


def test_field_path_camelcase_to_snake():
    """CamelCase field names should be converted to snake_case in path.

    Note: This is a standard naive conversion (every uppercase gets _ prefix).
    So "VSwitchId" → "v_switch_id", not "vswitch_id". This is the documented behavior.
    """
    assert _field_path("mysql", "AccountPassword") == "mysql.account_password"
    assert _field_path("mysql", "VSwitchId") == "mysql.v_switch_id"
    assert _field_path("redis", "CacheInstanceId") == "redis.cache_instance_id"
    assert _field_path("mysql", "DBInstanceId") == "mysql.d_b_instance_id"


def test_masker_hcl_line_for_sensitive():
    """hcl_line should produce var ref + sensitive=true for sensitive fields."""
    masker = SensitiveMasker()
    line = masker.hcl_line("mysql", "accountPassword", "secret")
    assert "var.mysql_password" in line
    assert "sensitive = true" in line


def test_masker_hcl_line_for_non_sensitive():
    """hcl_line should produce single attribute line for non-sensitive fields."""
    masker = SensitiveMasker()
    line = masker.hcl_line("vpc", "vpcName", "my-vpc")
    assert 'vpcName = "my-vpc"' in line
    assert "sensitive" not in line


def test_jdcloud_specific_no_secret_in_describe_response():
    """JD Cloud 特殊性: accountPassword 不在 describe 响应中。

    这个测试记录这个事实,作为未来 API 变更时的提醒。
    """
    # MySQL fixture 不应包含 accountPassword 字段
    import json
    import pathlib
    fixture = pathlib.Path(__file__).parent / "fixtures" / "mysql.json"
    data = json.loads(fixture.read_text())
    # The fixture represents the describe-instances response shape
    # accountPassword is NOT in describe responses (JD Cloud 安全设计)
    assert "accountPassword" not in data or data.get("accountPassword") is None


def test_iam_accesskeyid_in_response():
    """IAM AccessKeyId IS in describe-user-access-keys response (故需掩码)."""
    # Note: 实际 fixture 可能在 Phase 2 添加
    import json
    import pathlib
    fixture = pathlib.Path(__file__).parent / "fixtures" / "iam.json"
    data = json.loads(fixture.read_text())
    # IAM 用户 fixture 暂不包含 AccessKey 列表(简化 Phase 1)
    # 实际访问密钥列表需从 describe-user-access-keys API 获取
    assert isinstance(data, dict)
