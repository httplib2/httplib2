import subprocess
import sys
from pathlib import Path

import pytest

from httplib2.decode import DecoderProtocol


class EchoDecoder(DecoderProtocol):
    needs_input = True

    def decode(self, data):
        return data

    def flush(self):
        return b"tail"


@pytest.mark.parametrize("data", [b"", b"data"])
def test_consume_bytes_zero_chunk_preserves_input_and_flush(data):
    assert EchoDecoder().consume_bytes(data, 0) == data + b"tail"


def test_zero_limit_chunk_makes_progress_and_enforces_limits():
    script = """
import zlib
from httplib2.decode import LimitDecoder, ZlibDecoder, DecodeLimitError
data = zlib.compress(b'content')
decoder = LimitDecoder(ZlibDecoder(), chunk_size=0)
assert decoder.consume_bytes(data) == b'content'
decoder = LimitDecoder(ZlibDecoder(), chunk_size=0, hard_limit=3)
try:
    decoder.consume_bytes(data)
except DecodeLimitError:
    pass
else:
    raise AssertionError('hard limit was not enforced')
"""
    subprocess.run([sys.executable, "-B", "-c", script], check=True, capture_output=True,
                   cwd=str(Path(__file__).resolve().parents[1]), timeout=5)
