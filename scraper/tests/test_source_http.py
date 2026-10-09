import unittest
from unittest.mock import patch

from requests import Response
from requests.adapters import HTTPAdapter

from sources import garenspinnerij, uitgouda
from sources.http import SourceSession, get_source_page


def response(request, content=b"", status=200, location=None):
    result = Response()
    result.request = request
    result.url = request.url
    result.status_code = status
    result._content = content
    if location is not None:
        result.headers["Location"] = location
    return result


class SourceHttpTests(unittest.TestCase):
    def test_untrusted_destinations_never_reach_transport(self):
        urls = (
            "http://uitgouda.com/event/1",
            "https://127.0.0.1/internal",
            "https://[::1]/internal",
            "https://other.invalid/event/1",
            "https://uitgouda.com.other.invalid/event/1",
            "https://uitgouda.com:8443/event/1",
            "https://user:password@uitgouda.com/event/1",
        )
        with SourceSession(uitgouda.SOURCE_URL) as session:
            session.trust_env = False
            with patch.object(HTTPAdapter, "send") as transport:
                for url in urls:
                    with self.subTest(url=url):
                        with self.assertRaisesRegex(ValueError, "toegestane HTTPS-bron"):
                            session.get(url, timeout=30)
                transport.assert_not_called()

    def test_source_requests_preserve_post_and_timeout(self):
        with SourceSession("https://goudabruist.nl") as session:
            session.trust_env = False
            with patch.object(
                HTTPAdapter, "send",
                side_effect=lambda request, **kwargs: response(request),
            ) as transport:
                session.post("https://goudabruist.nl/activiteiten", data="", timeout=30)
                self.assertEqual(transport.call_args.args[0].method, "POST")
                self.assertEqual(transport.call_args.kwargs["timeout"], 30)

    def test_canonical_source_redirect_is_allowed(self):
        def send(request, **kwargs):
            if request.url == "https://uitgouda.com/events/":
                return response(request, status=302, location="https://www.uitgouda.com/events/")
            return response(request, b"source page")

        with patch.object(HTTPAdapter, "send", side_effect=send) as transport:
            result = get_source_page(uitgouda.SOURCE_URL, uitgouda.SOURCE_URL, timeout=30)
        self.assertEqual(result.url, "https://www.uitgouda.com/events/")
        self.assertEqual(transport.call_count, 2)

    def test_off_source_and_insecure_redirects_are_blocked_before_transport(self):
        for destination in ("https://127.0.0.1/internal", "http://uitgouda.com/events/"):
            with self.subTest(destination=destination):
                with patch.object(
                    HTTPAdapter, "send",
                    side_effect=lambda request, **kwargs: response(
                        request, status=302, location=destination,
                    ),
                ) as transport:
                    with self.assertRaisesRegex(ValueError, "toegestane HTTPS-bron"):
                        get_source_page(uitgouda.SOURCE_URL, uitgouda.SOURCE_URL, timeout=30)
                self.assertEqual(transport.call_count, 1)

    def test_untrusted_event_link_is_blocked_before_fetch(self):
        html = (
            b'<article class="event-card"><h3>Test</h3>'
            b'<a class="event-card-link" href="https://127.0.0.1/internal"></a></article>'
        )
        with patch.object(
            HTTPAdapter, "send",
            side_effect=lambda request, **kwargs: response(request, html),
        ) as transport:
            with self.assertRaisesRegex(ValueError, "toegestane HTTPS-bron"):
                uitgouda.fetch_events()
        self.assertEqual(transport.call_count, 1)

    def test_untrusted_pagination_link_is_blocked_before_fetch(self):
        html = (
            b'<main><div class="w-grid us_post_list">'
            b'<a class="next page-numbers" href="https://127.0.0.1/internal">Next</a>'
            b'</div></main>'
        )
        with patch.object(
            HTTPAdapter, "send",
            side_effect=lambda request, **kwargs: response(request, html),
        ) as transport:
            with self.assertRaisesRegex(ValueError, "toegestane HTTPS-bron"):
                garenspinnerij.fetch_events()
        self.assertEqual(transport.call_count, 1)


if __name__ == "__main__":
    unittest.main()
