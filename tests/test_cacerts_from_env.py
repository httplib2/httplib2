import os
import mock
import httplib2

CA_CERTS_BUILTIN = os.path.join(os.path.dirname(httplib2.__file__), "cacerts.txt")
ENV_CERTS_FILE = "unittest_env_certs_file"
CERTIFI_CERTS_FILE = "unittest_certifi_file"


@mock.patch("httplib2.certs.certifi_where")
def test_certs_file_from_builtin(certifi_mock):
    certifi_mock.return_value = None
    assert httplib2.certs.where() == CA_CERTS_BUILTIN


@mock.patch("httplib2.certs.certifi_where")
def test_certs_file_from_environment(certifi_mock):
    certifi_mock.return_value = None
    os.environ["HTTPLIB2_CA_CERTS"] = ENV_CERTS_FILE
    assert httplib2.certs.where() == ENV_CERTS_FILE
    os.environ.pop("HTTPLIB2_CA_CERTS")
    assert httplib2.certs.where() == CA_CERTS_BUILTIN


@mock.patch("httplib2.certs.certifi_where")
def test_certs_file_from_certifi(certifi_mock):
    certifi_mock.return_value = CERTIFI_CERTS_FILE
    assert httplib2.certs.where() == CERTIFI_CERTS_FILE
    certifi_mock.return_value = None
    assert httplib2.certs.where() == CA_CERTS_BUILTIN
