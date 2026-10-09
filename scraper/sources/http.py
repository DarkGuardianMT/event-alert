"""Beperk scraperverzoeken tot de ingestelde HTTPS-bron."""

from urllib.parse import urlsplit

import requests


class SourceSession(requests.Session):
    def __init__(self, source_url):
        super().__init__()
        host = urlsplit(source_url).hostname
        base_host = host[4:] if host.startswith("www.") else host
        self.allowed_hosts = {base_host, "www." + base_host}

    def send(self, request, **kwargs):
        # Ook automatische omleidingen komen hier langs, vóór het netwerkverzoek.
        parts = urlsplit(request.url)
        if (
            parts.scheme != "https"
            or parts.hostname not in self.allowed_hosts
            or parts.port not in (None, 443)
            or parts.username is not None
            or parts.password is not None
        ):
            raise ValueError("Scraper-URL valt buiten de toegestane HTTPS-bron.")
        return super().send(request, **kwargs)


def get_source_page(source_url, url, **kwargs):
    with SourceSession(source_url) as session:
        return session.get(url, **kwargs)
