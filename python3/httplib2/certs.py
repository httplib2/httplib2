"""
certs

Returns the path to the ca bundle from ca_certs_locater if available, or
from certifi, if available, or the environmental variable HTTPLIB2_CA_CERTS,
if available, or the default CA certificates file bundled with httplib2.

Code originally from Requests library by Kenneth Reitz.

"""
__version__ = "1.0.0"
__license__ = "MIT"
__history__ = """
"""

import os
import os.path

try:
    from certifi import where as get_cacerts
except ImportError:
    def get_cacerts():
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "cacerts.txt")


def where():
    return os.getenv('HTTPLIB2_CA_CERTS', get_cacerts())


if __name__ == '__main__':
    print(where())
