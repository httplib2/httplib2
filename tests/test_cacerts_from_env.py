import os
import sys
import mock
import httplib2

CA_CERTS_BUILTIN = os.path.join(os.path.dirname(httplib2.__file__), "cacerts.txt")
ENV_CERTS_FILE = "unittest_env_certs_file"
CERTIFI_CERTS_FILE = "unittest_certifi_file"
CUSTOM_CA_CERTS = "unittest_custom_ca_certs"


@mock.patch("httplib2.certs.certifi_available", False)
@mock.patch("httplib2.certs.custom_ca_locater_available", False)
def test_certs_file_from_builtin():
    assert httplib2.certs.where() == CA_CERTS_BUILTIN


@mock.patch("httplib2.certs.certifi_available", False)
@mock.patch("httplib2.certs.custom_ca_locater_available", False)
def test_certs_file_from_environment():
    os.environ["HTTPLIB2_CA_CERTS"] = ENV_CERTS_FILE
    assert httplib2.certs.where() == ENV_CERTS_FILE
    os.environ["HTTPLIB2_CA_CERTS"] = ""
    assert httplib2.certs.where() == CA_CERTS_BUILTIN
    os.environ.pop("HTTPLIB2_CA_CERTS")
    assert httplib2.certs.where() == CA_CERTS_BUILTIN


@mock.patch("httplib2.certs.certifi_available", True)
@mock.patch("httplib2.certs.custom_ca_locater_available", False)
def test_certs_file_from_certifi():
    certifi_mock = mock.MagicMock()
    certifi_mock.return_value = CERTIFI_CERTS_FILE
    httplib2.certs.certifi_where = certifi_mock
    assert httplib2.certs.where() == CERTIFI_CERTS_FILE


@mock.patch("httplib2.certs.certifi_available", False)
@mock.patch("httplib2.certs.custom_ca_locater_available", True)
def test_certs_file_from_custom_getter():
    custom_ca_mock = mock.MagicMock()
    custom_ca_mock.return_value = CUSTOM_CA_CERTS
    httplib2.certs.custom_ca_locater_where = custom_ca_mock
    assert httplib2.certs.where() == CUSTOM_CA_CERTS


@mock.patch("httplib2.certs.certifi_available", False)
@mock.patch("httplib2.certs.custom_ca_locater_available", False)
def test_with_certifi_removed_from_modules():
    if "certifi" in sys.modules:
        del sys.modules["certifi"]
    os.environ["HTTPLIB2_CA_CERTS"] = ENV_CERTS_FILE
    assert httplib2.certs.where() == ENV_CERTS_FILE
    os.environ.pop("HTTPLIB2_CA_CERTS")
    assert httplib2.certs.where() == CA_CERTS_BUILTIN
