"""
certs

Returns the path to the ca bundle from the environmental variable
HTTPLIB2_CA_CERTS, or from ca_certs_locater if available, or
from certifi, if available, or the default CA certificates file
bundled with httplib2.

Code originally from Requests library by Kenneth Reitz.

"""
__version__ = "1.0.0"
__license__ = "MIT"
__history__ = """
"""

import os


def custom_ca_certs_get():
    return None


try:
    from ca_certs_locater import get as custom_ca_certs_get
except ImportError:
    pass


def certifi_where():
    return None


try:
    from certifi import where as certifi_where
except ImportError:
    pass

BUILTIN_CA_CERTS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "cacerts.txt"
)


def where():
    env = os.environ.get("HTTPLIB2_CA_CERTS")
    if env: # if not None and != ""
        return env
    if custom_ca_certs_get():
        return custom_ca_certs_get()
    if certifi_where():
        return certifi_where()
    return BUILTIN_CA_CERTS


if __name__ == "__main__":
    print(where())
