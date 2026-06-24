import pytest

import httplib2
from httplib2.decode import LimitDecoder, ZlibDecoder, DecodeLimitError, DecodeRatioError
import tests


def test_gzip_head():
    # Test that we don't try to decompress a HEAD response
    http = httplib2.Http()
    response = tests.http_response_bytes(headers={"content-encoding": "gzip", "content-length": 42})
    with tests.server_const_bytes(response) as uri:
        response, content = http.request(uri, "HEAD")
        assert response.status == 200
        assert int(response["content-length"]) != 0
        assert content == b""


def test_gzip_get():
    # Test that we support gzip compression
    http = httplib2.Http()
    response = tests.http_response_bytes(
        headers={"content-encoding": "gzip"},
        body=tests.gzip_compress(b"properly compressed"),
    )
    with tests.server_const_bytes(response) as uri:
        response, content = http.request(uri, "GET")
        assert response.status == 200
        assert "content-encoding" not in response
        assert "-content-encoding" in response
        assert int(response["content-length"]) == len(b"properly compressed")
        assert content == b"properly compressed"


def test_gzip_post_response():
    http = httplib2.Http()
    response = tests.http_response_bytes(
        headers={"content-encoding": "gzip"},
        body=tests.gzip_compress(b"properly compressed"),
    )
    with tests.server_const_bytes(response) as uri:
        response, content = http.request(uri, "POST", body=b"")
        assert response.status == 200
        assert "content-encoding" not in response
        assert "-content-encoding" in response


def test_gzip_malformed_response():
    http = httplib2.Http()
    # Test that we raise a good exception when the gzip fails
    http.force_exception_to_status_code = False
    response = tests.http_response_bytes(headers={"content-encoding": "gzip"}, body=b"obviously not compressed")
    with tests.server_const_bytes(response, request_count=2) as uri:
        with tests.assert_raises(httplib2.FailedToDecompressContent):
            http.request(uri, "GET")

        # Re-run the test with out the exceptions
        http.force_exception_to_status_code = True

        response, content = http.request(uri, "GET")
        assert response.status == 500
        assert response.reason.startswith("Content purported")


def test_deflate_get():
    # Test that we support deflate compression
    http = httplib2.Http()
    response = tests.http_response_bytes(
        headers={"content-encoding": "deflate"},
        body=tests.deflate_compress(b"properly compressed"),
    )
    with tests.server_const_bytes(response) as uri:
        response, content = http.request(uri, "GET")
        assert response.status == 200
        assert "content-encoding" not in response
        assert int(response["content-length"]) == len(b"properly compressed")
        assert content == b"properly compressed"


def test_deflate_malformed_response():
    # Test that we raise a good exception when the deflate fails
    http = httplib2.Http()
    http.force_exception_to_status_code = False
    response = tests.http_response_bytes(headers={"content-encoding": "deflate"}, body=b"obviously not compressed")
    with tests.server_const_bytes(response, request_count=2) as uri:
        with tests.assert_raises(httplib2.FailedToDecompressContent):
            http.request(uri, "GET")

        # Re-run the test with out the exceptions
        http.force_exception_to_status_code = True

        response, content = http.request(uri, "GET")
        assert response.status == 500
        assert response.reason.startswith("Content purported")


def test_zlib_get():
    # Test that we support zlib compression
    http = httplib2.Http()
    response = tests.http_response_bytes(
        headers={"content-encoding": "deflate"},
        body=tests.zlib_compress(b"properly compressed"),
    )
    with tests.server_const_bytes(response) as uri:
        response, content = http.request(uri, "GET")
        assert response.status == 200
        assert "content-encoding" not in response
        assert int(response["content-length"]) == len(b"properly compressed")
        assert content == b"properly compressed"


def test_gzip_excess_ratio():
    http = httplib2.Http()
    original = b"\x00" * (50 << 20)  # 50 MiB to ~50 KiB
    response = tests.http_response_bytes(
        headers={"content-encoding": "gzip"},
        body=tests.gzip_compress(original),
    )
    with tests.server_const_bytes(response) as uri:
        try:
            http.request(uri, "GET")
            assert False, "expected DecodeRatioError"
        except DecodeRatioError:
            pass


@pytest.mark.parametrize("safe_limit", (0, 1000, 20000))
def test_limitdecoder_normal_decompression_no_limits(safe_limit):
    """Standard decompression of random data should pass with any safe_limit"""
    original = tests.randbytes(10 << 10)
    compressed = tests.zlib_compress(original)

    decoder = LimitDecoder(
        ZlibDecoder(),
        ratio=10,
        safe_limit=safe_limit,
        hard_limit=len(original) + 1,
    )
    result = decoder.consume_bytes(compressed)
    assert result == original
    assert decoder._output_length == len(original)


def test_limitdecoder_normal_rechunking():
    """Passing a massive single chunk should be re-chunked internally without error"""
    original = b"\x00" * (10 << 20)
    compressed = tests.zlib_compress(original)
    assert len(compressed) > 2000

    decoder = LimitDecoder(
        ZlibDecoder(),
        ratio=2000,
        chunk_size=512,
        safe_limit=0,
        hard_limit=len(original) + 1,
    )
    result = decoder.consume_bytes(compressed, chunk_size=0)
    assert result == original
    assert decoder._consumed_length == len(compressed)


def test_limitdecoder_amplification_ratio_exceeded():
    """High ratio should trigger DecodeRatioError above safe_limit"""
    original = b"\x00" * (1 << 20)
    compressed = tests.zlib_compress(original)

    decoder = LimitDecoder(
        ZlibDecoder(),
        ratio=10,
        chunk_size=512,
        safe_limit=0,
        hard_limit=len(original) + 1,
    )
    try:
        decoder.consume_bytes(compressed, chunk_size=0)
        assert False, "expected DecodeRatioError"
    except DecodeRatioError:
        pass
    assert decoder._consumed_length == 512, "expected ratio error on first chunk"


@pytest.mark.parametrize("ratio", (0, 10, 1000))
def test_limitdecoder_hard_limit_exceeded(ratio):
    """Output exceeding hard_limit must trigger DecodeLimitError regardless of ratio"""
    original = b"\x00" * (10 << 10)
    compressed = tests.zlib_compress(original)

    decoder = LimitDecoder(
        ZlibDecoder(),
        ratio=ratio,
        safe_limit=0,
        hard_limit=len(original) - 1,
    )
    try:
        decoder.consume_bytes(compressed)
        assert False, "expected DecodeLimitError"
    except DecodeLimitError:
        pass


@pytest.mark.parametrize("ratio", (0, 10, 1000))
def test_limitdecoder_safe_limit_bypass(ratio):
    """Any ratio allowed if total output < safe_limit"""
    original = b"\x00" * (10 << 10)
    compressed = tests.zlib_compress(original)

    decoder = LimitDecoder(
        ZlibDecoder(),
        ratio=ratio,
        safe_limit=len(original) + 1,
        hard_limit=len(original) + 1,
    )
    result = decoder.consume_bytes(compressed)
    assert result == original
    assert decoder._output_length == len(original)


def test_limitdecoder_single_byte_feeding():
    """Feeding compressed data 1 byte at a time should still decode correctly"""
    original = tests.randbytes(10 << 10)
    compressed = tests.zlib_compress(original)

    decoder = LimitDecoder(
        ZlibDecoder(),
        ratio=10,
        safe_limit=5 << 10,
        hard_limit=len(original) + 1,
    )
    result = decoder.consume_bytes(compressed, chunk_size=1)
    assert result == original


def test_limitdecoder_invalid_argument():
    checks = (
        ("ratio", dict(ratio=-1)),
        ("chunk_size", dict(chunk_size=-1)),
        ("safe_limit", dict(safe_limit=-1)),
        ("hard_limit", dict(hard_limit=-1)),
    )
    for name, check in checks:
        zd = ZlibDecoder()
        try:
            LimitDecoder(zd, **check)
            assert False, f"check={name} expected ValueError"
        except ValueError as e:
            assert "expected >= 0" in str(e).lower(), str(e)


def test_zlibdecoder_invalid_after_flush():
    checks = (
        ("needs_input", lambda d: d.needs_input),
        ("decode", lambda d: d.decode(b"")),
        ("flush", lambda d: d.flush()),
    )
    for name, check in checks:
        d = ZlibDecoder()
        d.decode(tests.zlib_compress(b""))
        d.flush()
        try:
            check(d)
            assert False, f"check={name} expected RuntimeError"
        except RuntimeError as e:
            assert "used after flush" in str(e).lower(), str(e)
