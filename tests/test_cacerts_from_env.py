import os
import httplib2

try:
    import certifi
    CA_CERTS_FILE = certifi.where()
except ImportError as e:
    CA_CERTS_FILE = os.path.join(
        os.path.dirname(httplib2.__file__), 'cacerts.txt')


def test_certs_file_from_default_location():
    assert httplib2.certs.where() == CA_CERTS_FILE


def test_certs_file_from_environment():
    os.environ["HTTPLIB2_CA_CERTS"] = "unittest_test_certs_file"
    assert httplib2.certs.where() == "unittest_test_certs_file"
    os.environ.pop("HTTPLIB2_CA_CERTS")
    assert httplib2.certs.where() == CA_CERTS_FILE
