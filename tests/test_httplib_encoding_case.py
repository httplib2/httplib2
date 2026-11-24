import gzip
import zlib

import httplib2
import pytest


@pytest.mark.parametrize("coding,compress", [
    ("GZip", gzip.compress),
    ("GZIP", gzip.compress),
    (" GZip ", gzip.compress),
    ("DeFlAtE", zlib.compress),
    ("ZLIB", zlib.compress),
])
def test_content_coding_is_case_insensitive(coding, compress):
    content = b"decoded response"
    response = httplib2.Response({"status": "200", "content-encoding": coding})
    assert httplib2._decompressContent(response, compress(content), {}) == content
    assert response["content-length"] == str(len(content))
    assert response["-content-encoding"] == coding
    assert "content-encoding" not in response


def test_raw_deflate_coding_is_case_insensitive():
    content = b"raw response"
    compressor = zlib.compressobj(wbits=-15)
    encoded = compressor.compress(content) + compressor.flush()
    response = httplib2.Response({"status": "200", "content-encoding": "DEFLATE"})
    assert httplib2._decompressContent(response, encoded, {}) == content


def test_unknown_content_coding_is_preserved():
    response = httplib2.Response({"status": "200", "content-encoding": "custom"})
    assert httplib2._decompressContent(response, b"opaque", {}) == b"opaque"
    assert response["content-encoding"] == "custom"
