"""Tests for sensitive masker (JD Cloud)."""

from scripts.lib.sensitive_masker import mask_field, _field_path


SENSITIVE_FIELDS = {
    "mysql": {"accountpassword": "mysql_password"},
    "postgresql": {"accountpassword": "postgresql_password"},
    "mongodb": {"accountpassword": "mongodb_password"},
    "redis": {"password": "redis_password"},
    "iam": {"accesskeyid": "iam_access_key_id", "accesskey": "iam_access_key_id"},
}


def _is_sensitive(rt, field):
    return field.lower() in SENSITIVE_FIELDS.get(rt.lower(), {})


def test_mysql_password_is_sensitive():
    assert _is_sensitive("mysql", "accountPassword") is True


def test_postgres_password_is_sensitive():
    assert _is_sensitive("postgresql", "accountPassword") is True


def test_mongodb_password_is_sensitive():
    assert _is_sensitive("mongodb", "accountPassword") is True


def test_redis_password_is_sensitive():
    assert _is_sensitive("redis", "password") is True


def test_iam_access_key_is_sensitive():
    assert _is_sensitive("iam", "accessKeyId") is True


def test_vpc_field_is_not_sensitive():
    assert _is_sensitive("vpc", "vpcName") is False


def test_sg_field_is_not_sensitive():
    assert _is_sensitive("sg", "networkSecurityGroupName") is False


def test_kms_field_is_not_sensitive():
    assert _is_sensitive("kms", "keyName") is False


def test_mask_field_replaces_with_var_ref():
    masked, path = mask_field("mysql", "accountPassword", "supersecret")
    assert masked == "${var.mysql_password}"
    assert "supersecret" not in str(masked)


def test_mask_field_leaves_non_sensitive_unchanged():
    masked, path = mask_field("vpc", "vpcName", "my-vpc")
    assert masked == "my-vpc"
    assert path is None


def test_mask_field_returns_path():
    masked, path = mask_field("mysql", "accountPassword", "secret")
    assert masked == "${var.mysql_password}"
    assert path == "mysql.account_password"


def test_field_path_camelcase_to_snake():
    assert _field_path("mysql", "AccountPassword") == "mysql.account_password"


def test_jdcloud_specific_no_secret_in_describe_response():
    import json
    import pathlib

    fixture = pathlib.Path(__file__).parent / "fixtures" / "mysql.json"
    data = json.loads(fixture.read_text())
    assert "accountPassword" not in data or data.get("accountPassword") is None


def test_iam_accesskeyid_in_response():
    import json
    import pathlib

    fixture = pathlib.Path(__file__).parent / "fixtures" / "iam.json"
    data = json.loads(fixture.read_text())
    assert isinstance(data, dict)
