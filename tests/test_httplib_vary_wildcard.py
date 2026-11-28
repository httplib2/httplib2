import httplib2
import pytest
import tests


@pytest.mark.parametrize("vary", ["*", "Accept, *", "Accept, \t*\t"])
def test_vary_wildcard_cannot_satisfy_only_if_cached(tmp_path, vary):
    http = httplib2.Http(cache=str(tmp_path))
    with tests.server_const_http(
            headers={"vary": vary, "cache-control": "max-age=300"}, add_date=True) as uri:
        first, _ = http.request(uri, headers={"accept": "text/plain"})
        assert first.status == 200
        response, _ = http.request(uri, headers={
            "accept": "text/plain", "cache-control": "only-if-cached",
        })
        assert response.status == 504
        assert not response.fromcache


def test_ordinary_vary_can_still_match(tmp_path):
    http = httplib2.Http(cache=str(tmp_path))
    with tests.server_const_http(
            headers={"vary": "Accept", "cache-control": "max-age=300"}, add_date=True) as uri:
        http.request(uri, headers={"accept": "text/plain"})
        response, _ = http.request(uri, headers={
            "accept": "text/plain", "cache-control": "only-if-cached",
        })
        assert response.status == 200
        assert response.fromcache
