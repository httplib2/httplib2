import sys
import httplib2
import atheris
import tests


def TestOneInput(input_bytes):
    http = httplib2.Http()
    ib = b"HTTP/1.0 200 OK\r\n" + input_bytes
    with tests.server_const_bytes(ib) as uri:
        http.request(uri)


def main():
    atheris.Setup(sys.argv, TestOneInput, enable_python_coverage=True)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
