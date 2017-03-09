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
    # Users can optionally provide a module that tells us where the CA_CERTS
    # are located.
    from ca_certs_locater import get as where
except ImportError:
    try:
        from certifi import where
    except ImportError:
        def where():
            certpath = os.getenv('HTTPLIB2_CA_CERTS', os.path.join(
                os.path.dirname(os.path.abspath(__file__ )), "cacerts.txt"))

            return certpath

if __name__ == '__main__':
    print(where())