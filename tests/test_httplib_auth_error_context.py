import httplib2
import pytest


@pytest.mark.parametrize("authentication,challenge,error_type", [
    (httplib2.DigestAuthentication,
     'Digest realm="example", nonce="n", qop="auth-int"',
     httplib2.UnimplementedDigestAuthOptionError),
    (httplib2.DigestAuthentication,
     'Digest realm="example", nonce="n", algorithm="unsupported"',
     httplib2.UnimplementedDigestAuthOptionError),
    (httplib2.HmacDigestAuthentication,
     'HMACDigest realm="example"',
     httplib2.UnimplementedHmacDigestAuthOptionError),
    (httplib2.HmacDigestAuthentication,
     'HMACDigest realm="example", snonce="n", algorithm="unsupported"',
     httplib2.UnimplementedHmacDigestAuthOptionError),
    (httplib2.HmacDigestAuthentication,
     'HMACDigest realm="example", snonce="n", pw-algorithm="unsupported"',
     httplib2.UnimplementedHmacDigestAuthOptionError),
])
def test_unsupported_authentication_options_keep_response_context(authentication, challenge, error_type):
    response = {"www-authenticate": challenge}
    content = b"authentication details"
    with pytest.raises(error_type) as caught:
        authentication(("user", "password"), "example.com", "/", {}, response, content, httplib2.Http())
    assert caught.value.response is response
    assert caught.value.content is content
    assert str(caught.value)
