Introduction
============

httplib2 is a comprehensive HTTP client library, httplib2.py supports many
features left out of other HTTP libraries.

If you want to help this project by bug report or code change, [contribution guidelines](contributing.md) may contain useful information.

### HTTP and HTTPS

HTTPS support is only available if the socket module was
compiled with SSL support.

### Keep-Alive

Supports HTTP 1.1 Keep-Alive, keeping the socket open and
performing multiple requests over the same connection if
possible.

### Authentication

The following three types of HTTP Authentication are
supported. These can be used over both HTTP and HTTPS.

* Digest
* Basic
* WSSE

### Caching

The module can optionally operate with a private cache that
understands the Cache-Control: header and uses both the ETag
and Last-Modified cache validators.

### All Methods

The module can handle any HTTP request method, not just GET
and POST.

### Redirects

Automatically follows 3XX redirects on GETs.

### Compression

Handles both 'deflate' and 'gzip' types of compression.

### Lost update support

Automatically adds back ETags into PUT requests to resources
we have already cached. This implements Section 3.2 of
Detecting the Lost Update Problem Using Unreserved Checkout.

### Unit Tested

A large and growing set of unit tests.


Installation
============


    $ pip install httplib2


Strings vs bytes
================

To successfully use http2lib, you absolutely must understand the following sentence:

**The headers are strings, but the content body is bytes.**


Usage
=====

A simple retrieval:

```python
import httplib2
h = httplib2.Http(".cache")
(resp_headers, content) = h.request("http://example.org/", "GET")
```

The 'content' is the content retrieved from the URL. The content
is already decompressed or unzipped if necessary.

To PUT some content to a server that uses SSL and Basic authentication:

```python
import httplib2
h = httplib2.Http(".cache")
h.add_credentials('name', 'password')
(resp, content) = h.request("https://example.org/chapter/2",
                            "PUT", body="This is text",
                            headers={'content-type':'text/plain'} )
```

Use the Cache-Control: header to control how the caching operates.

```python
import httplib2
h = httplib2.Http(".cache")
(resp, content) = h.request("http://bitworking.org/", "GET")
...
(resp, content) = h.request("http://bitworking.org/", "GET",
                            headers={'cache-control':'no-cache'})
```

The first request will be cached and since this is a request
to bitworking.org it will be set to be cached for two hours,
because that is how I have my server configured. Any subsequent
GET to that URI will return the value from the on-disk cache
and no request will be made to the server. You can use the
Cache-Control: header to change the caches behavior and in
this example the second request adds the Cache-Control:
header with a value of 'no-cache' which tells the library
that the cached copy must not be used when handling this request.

More example usage can be found at:

 * https://github.com/httplib2/httplib2/wiki/Examples
 * https://github.com/httplib2/httplib2/wiki/Examples-Python3


### Decompression Limits

To mitigate denial-of-service risks from maliciously crafted compressed responses, the library enforces configurable limits during decompression. Limits are checked in fixed order: **hard limit** → **safe limit** → **ratio**.

- **hard limit**
  Absolute maximum decompressed output size (bytes). Exceeding it raises `DecodeLimitError`. Default: `10 GiB`.
- **safe limit**
  Output size below which the ratio check is skipped (avoids false positives on small payloads). Default: `10 MiB`.
- **ratio**
  Maximum allowed inflation factor (`output_bytes ÷ consumed_input_bytes`). Once output exceeds `safe_limit`, the ratio is enforced. Default: `100`.
- **chunk size**
  Internal processing chunk size in bytes (affects granularity of limit checks). Default: `65536` (64 KiB).

Configuration priority (highest first):
1. `Http()` constructor arguments: `decode_limit_hard`, `decode_limit_safe`, `decode_limit_ratio`, `decode_limit_chunk`
2. Environment variables: `httplib2_decode_limit_hard`, `httplib2_decode_limit_safe`, `httplib2_decode_limit_ratio`, `httplib2_decode_limit_chunk` (case-insensitive, uppercase also accepted)
3. Library defaults (listed above)

Example:
```python
h = Http(decode_limit_hard=50_000_000, decode_limit_ratio=50)
```

### CA Certificates

HTTPS server certificates are verified against the first CA bundle found, in this order:

1. `Http(ca_certs=...)` constructor argument
2. `HTTPLIB2_CA_CERTS` environment variable (path to a PEM file)
3. `ca_certs_locater` package, if installed
4. `certifi` package, if installed
5. `cacerts.txt` bundled with httplib2

Items 2-5 are resolved once, when httplib2 is imported. Setting or changing `HTTPLIB2_CA_CERTS` after import has no effect,
and if it names a file that does not exist, `import httplib2` raises `RuntimeError`.

The bundled file is a snapshot and only changes with httplib2 releases.
Installing a current `certifi` (`pip install -U certifi`) is the easiest way to receive CA trust updates sooner.

#### eMudhra intermediates (October 2026)

Mozilla distrusted 16 compromised eMudhra intermediate CAs (bug 2083449).
httplib2 0.32.0 and earlier trust 8 of them through the Comodo "AAA Certificate Services" root in the bundled `cacerts.txt`.
0.32.1 replaces the bundle with certifi 2026.10.23, which trusts none of them.

Upgrading httplib2 only helps if the bundled file is actually used. If `ca_certs_locater` or `certifi` is installed,
that bundle is used instead, and certifi releases older than 2026.10.23 may still trust some of these intermediates.
Check which bundle is in use with `python -c "import httplib2.certs; print(httplib2.certs.where())"`.

To fix this, with or without upgrading httplib2, do any one of:

- if `certifi` is installed (often pulled in by `requests` or `pip`): `pip install -U 'certifi>=2026.10.23'`
- if `ca_certs_locater` is installed: update the bundle it points to, or set `HTTPLIB2_CA_CERTS`, which takes precedence over it
- set `HTTPLIB2_CA_CERTS=/path/to/bundle.pem` to a bundle that does not trust these intermediates, before httplib2 is imported
- pass `Http(ca_certs="/path/to/bundle.pem")`

With httplib2 0.32.1 or later installed, its own bundled file is a clean choice for either of the last two,
and it overrides an old `certifi` or `ca_certs_locater`. Print its path with
`python -c "import httplib2.certs; print(httplib2.certs.BUILTIN_CA_CERTS)"` (0.32.0 and earlier ship the affected file).
