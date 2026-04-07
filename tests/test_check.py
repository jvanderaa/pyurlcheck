"""Tests for checks."""

from pyurlcheck.check import is_private, split_url


def test_split_url():
    result = split_url("https://www.google.com/path?q=1")
    assert result.scheme == "https"
    assert result.netloc == "www.google.com"
    assert result.path == "/path"
    assert result.query == "q=1"


def test_split_url_no_scheme():
    result = split_url("www.google.com")
    assert result.scheme == ""
    assert result.netloc == ""
    assert result.path == "www.google.com"


def test_is_private_rfc1918():
    assert is_private("192.168.1.1") is True
    assert is_private("10.0.0.1") is True
    assert is_private("172.16.0.1") is True


def test_is_private_public():
    assert is_private("8.8.8.8") is False
    assert is_private("1.1.1.1") is False
