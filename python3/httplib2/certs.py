"""
certs

Returns the path to the ca bundle from the environmental variable
HTTPLIB2_CA_CERTS, if available, or certifi, if available,
or the default CA certificates file bundled with httplib2.

Code originally from Requests library by Kenneth Reitz.

"""
__version__ = "1.0.0"
__license__ = "MIT"
__history__ = """
"""

import os


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
    if env is not None:
        return env
    if certifi_where() is not None:
        return certifi_where()
    return BUILTIN_CA_CERTS


if __name__ == "__main__":
    print(where())
