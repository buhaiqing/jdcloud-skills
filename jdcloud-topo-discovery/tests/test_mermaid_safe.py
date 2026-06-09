"""Tests for mermaid_safe — Mermaid rendering safety utilities."""
import pytest
from scripts.lib.mermaid_safe import (
    mermaid_escape,
    mermaid_safe_id,
    mermaid_safe_label,
    mermaid_extract_str,
    mermaid_safe_subgraph_label,
    mermaid_safe_vpc_label,
)


# ── mermaid_escape ──

@pytest.mark.parametrize("input_text,expected", [
    # Parentheses
    ("丹东鹏飞 (vpc-xxx)", "丹东鹏飞 &#40;vpc-xxx&#41;"),
    ("(test)", "&#40;test&#41;"),
    # Square brackets
    ("[label]", "&#91;label&#93;"),
    # Curly braces
    ("{key}", "&#123;key&#125;"),
    # Pipe
    ("App | 10.0.0.0/24", "App &#124; 10.0.0.0/24"),
    # Double quotes
    ('say "hello"', "say &quot;hello&quot;"),
    # Line break
    ("line1\\nline2", "line1<br/>line2"),
    # Combined
    ("丹东鹏飞 (vpc-xxx) | 10.0.0.0/24",
     "丹东鹏飞 &#40;vpc-xxx&#41; &#124; 10.0.0.0/24"),
    # No special chars
    ("simple-label", "simple-label"),
    # Empty
    ("", ""),
])
def test_mermaid_escape(input_text, expected):
    assert mermaid_escape(input_text) == expected


def test_mermaid_escape_non_string():
    """Non-string inputs should be converted to string."""
    assert mermaid_escape(123) == "123"
    assert mermaid_escape(None) == "None"


# ── mermaid_safe_id ──

@pytest.mark.parametrize("input_id,expected", [
    ("res_alb-z5aeeqhdtj", "res_alb-z5aeeqhdtj"),
    ("res_redis-jq8j5c6slnfd", "res_redis-jq8j5c6slnfd"),
    ("sub_subnet-whicj3hhk0", "sub_subnet-whicj3hhk0"),
    # Dots replaced
    ("eip_116.196.75.209", "eip_116_196_75_209"),
    # Special chars replaced
    ("res_alb-z5aeeqhdtj:test", "res_alb-z5aeeqhdtj_test"),
    ("agg_abc-def_123", "agg_abc-def_123"),
    # Chinese chars replaced
    ("res_鹏飞", "res___"),
])
def test_mermaid_safe_id(input_id, expected):
    assert mermaid_safe_id(input_id) == expected


# ── mermaid_safe_label ──

def test_mermaid_safe_label_basic():
    label = mermaid_safe_label("✅ my-app<br/>10.0.0.1")
    assert "✅ my-app<br/>10.0.0.1" in label


def test_mermaid_safe_label_with_special_chars():
    label = mermaid_safe_label("App (prod) | 10.0.0.0/24")
    assert "&#40;" in label
    assert "&#41;" in label
    assert "&#124;" in label


def test_mermaid_safe_label_truncation():
    long_text = "x" * 250
    label = mermaid_safe_label(long_text, max_len=100)
    assert len(label) <= 100
    assert label.endswith("...")


def test_mermaid_safe_label_no_truncation():
    short_text = "short label"
    label = mermaid_safe_label(short_text, max_len=200)
    assert label == mermaid_escape(short_text)


# ── mermaid_extract_str ──

def test_extract_flat_field():
    data = {"name": "test-vm"}
    assert mermaid_extract_str(data, "name") == "test-vm"


def test_extract_nested_field():
    data = {"privateIp": {"privateIpAddress": "10.0.0.1"}}
    assert mermaid_extract_str(data, "privateIp.privateIpAddress") == "10.0.0.1"


def test_extract_nested_field_not_string():
    """When the extracted value is a dict, return default."""
    data = {"privateIp": {"privateIpAddress": "10.0.0.1"}}
    assert mermaid_extract_str(data, "privateIp") == ""


def test_extract_missing_field():
    data = {"name": "test"}
    assert mermaid_extract_str(data, "missing") == ""


def test_extract_missing_nested_field():
    data = {"privateIp": {"privateIpAddress": "10.0.0.1"}}
    assert mermaid_extract_str(data, "privateIp.missing") == ""


def test_extract_custom_default():
    data = {}
    assert mermaid_extract_str(data, "missing", "N/A") == "N/A"


def test_extract_non_dict_intermediate():
    """When intermediate key is not a dict, return default."""
    data = {"privateIp": "not-a-dict"}
    assert mermaid_extract_str(data, "privateIp.privateIpAddress") == ""


# ── mermaid_safe_subgraph_label ──

def test_subgraph_label_basic():
    label = mermaid_safe_subgraph_label("鹏飞-应用生产", "172.21.14.32/27")
    assert "鹏飞-应用生产" in label
    assert "172.21.14.32/27" in label
    assert "&#124;" in label  # pipe escaped


def test_subgraph_label_with_az():
    label = mermaid_safe_subgraph_label("App", "10.0.0.0/24", "cn-north-1c")
    assert "App" in label
    assert "10.0.0.0/24" in label
    assert "cn-north-1c" in label


def test_subgraph_label_no_cidr():
    label = mermaid_safe_subgraph_label("App")
    assert label == mermaid_escape("App")


# ── mermaid_safe_vpc_label ──

def test_vpc_label():
    label = mermaid_safe_vpc_label("丹东鹏飞", "vpc-24lk5go6oj")
    assert "丹东鹏飞" in label
    assert "vpc-24lk5go6oj" in label
    assert "&#40;" in label  # ( escaped
    assert "&#41;" in label  # ) escaped


def test_vpc_label_no_special_chars():
    label = mermaid_safe_vpc_label("prod", "vpc-abc123")
    assert "&#40;prod&#41;" not in label  # name has no parens
    assert "vpc-abc123" in label
