from __future__ import annotations

import ipaddress
import socket
from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from cv_loader import load_single_cv


REQUEST_TIMEOUT = httpx.Timeout(
    15.0,
    connect=5.0,
    read=15.0,
    write=10.0,
    pool=5.0,
)

MAX_DOWNLOAD_BYTES = 10 * 1024 * 1024
MAX_REDIRECTS = 5
MAX_EXTRACTED_CHARACTERS = 100_000

ALLOWED_SCHEMES = {"http", "https"}
HTML_CONTENT_TYPES = {"text/html", "application/xhtml+xml"}
TEXT_CONTENT_TYPES = {"text/plain", "text/markdown", "text/csv"}
PDF_CONTENT_TYPES = {"application/pdf"}


@dataclass
class ExternalCandidateSource:
    source_url: str
    final_url: str
    source_type: str
    title: str
    content_type: str
    text: str
    downloaded_bytes: int

    def to_dict(self) -> dict:
        return asdict(self)


def _clean_content_type(value: str | None) -> str:
    return str(value or "").split(";", 1)[0].strip().lower()


def _is_public_ip(address: ipaddress._BaseAddress) -> bool:
    return bool(address.is_global)


def _resolve_public_addresses(hostname: str) -> list[str]:
    try:
        records = socket.getaddrinfo(
            hostname,
            None,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise ValueError(
            f"Unable to resolve hostname: {hostname}"
        ) from exc

    addresses = sorted(
        {
            record[4][0]
            for record in records
            if record and record[4]
        }
    )

    if not addresses:
        raise ValueError(
            f"No IP address was found for: {hostname}"
        )

    for value in addresses:
        address = ipaddress.ip_address(value)

        if not _is_public_ip(address):
            raise ValueError(
                "The URL resolves to a private, local, reserved, "
                "or otherwise non-public address."
            )

    return addresses


def validate_external_url(url: str) -> str:
    normalized = str(url or "").strip()

    if not normalized:
        raise ValueError("A URL is required.")

    parsed = urlparse(normalized)

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise ValueError(
            "Only http:// and https:// URLs are supported."
        )

    if not parsed.hostname:
        raise ValueError(
            "The URL must include a valid hostname."
        )

    if parsed.username or parsed.password:
        raise ValueError(
            "URLs containing embedded usernames or passwords "
            "are not allowed."
        )

    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError(
            "The URL contains an invalid port."
        ) from exc

    if port not in {None, 80, 443}:
        raise ValueError(
            "Only standard HTTP and HTTPS ports are allowed."
        )

    hostname = parsed.hostname.rstrip(".").lower()

    if hostname in {
        "localhost",
        "localhost.localdomain",
        "metadata.google.internal",
    }:
        raise ValueError(
            "Local and cloud metadata hostnames are not allowed."
        )

    try:
        literal_address = ipaddress.ip_address(hostname)
    except ValueError:
        _resolve_public_addresses(hostname)
    else:
        if not _is_public_ip(literal_address):
            raise ValueError(
                "Private, local, reserved, or non-public IP "
                "addresses are not allowed."
            )

    return normalized


def _iter_response_bytes(
    response: httpx.Response,
    maximum_bytes: int,
) -> tuple[bytes, int]:
    chunks: list[bytes] = []
    downloaded = 0

    for chunk in response.iter_bytes():
        if not chunk:
            continue

        downloaded += len(chunk)

        if downloaded > maximum_bytes:
            raise ValueError(
                "The remote file is larger than the "
                f"{maximum_bytes // (1024 * 1024)} MB limit."
            )

        chunks.append(chunk)

    return b"".join(chunks), downloaded


def download_external_content(
    url: str,
    *,
    maximum_bytes: int = MAX_DOWNLOAD_BYTES,
    maximum_redirects: int = MAX_REDIRECTS,
) -> dict:
    current_url = validate_external_url(url)
    redirect_count = 0

    headers = {
        "User-Agent": (
            "AIRS-Candidate-Importer/1.0 "
            "(authorized recruitment data import)"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/pdf,"
            "text/plain;q=0.9,*/*;q=0.5"
        ),
    }

    with httpx.Client(
        timeout=REQUEST_TIMEOUT,
        follow_redirects=False,
        verify=True,
        trust_env=False,
        headers=headers,
    ) as client:
        while True:
            validate_external_url(current_url)

            try:
                with client.stream("GET", current_url) as response:
                    if response.status_code in {
                        301,
                        302,
                        303,
                        307,
                        308,
                    }:
                        location = response.headers.get("location")

                        if not location:
                            raise ValueError(
                                "The server returned a redirect without "
                                "a destination."
                            )

                        redirect_count += 1

                        if redirect_count > maximum_redirects:
                            raise ValueError(
                                "The URL exceeded the maximum number "
                                "of redirects."
                            )

                        current_url = validate_external_url(
                            urljoin(current_url, location)
                        )
                        continue

                    response.raise_for_status()

                    declared_length = response.headers.get(
                        "content-length"
                    )

                    if declared_length:
                        try:
                            declared_size = int(declared_length)
                        except ValueError:
                            declared_size = 0

                        if declared_size > maximum_bytes:
                            raise ValueError(
                                "The remote file is larger than the "
                                f"{maximum_bytes // (1024 * 1024)} MB "
                                "limit."
                            )

                    body, downloaded = _iter_response_bytes(
                        response,
                        maximum_bytes,
                    )

                    return {
                        "requested_url": url,
                        "final_url": str(response.url),
                        "content_type": _clean_content_type(
                            response.headers.get("content-type")
                        ),
                        "body": body,
                        "downloaded_bytes": downloaded,
                    }

            except httpx.TimeoutException as exc:
                raise ValueError(
                    "The remote server took too long to respond."
                ) from exc
            except httpx.HTTPStatusError as exc:
                raise ValueError(
                    "The remote server returned HTTP "
                    f"{exc.response.status_code}."
                ) from exc
            except httpx.RequestError as exc:
                raise ValueError(
                    f"Unable to download the URL: {exc}"
                ) from exc


def _remove_unhelpful_html(soup: BeautifulSoup) -> None:
    for tag_name in [
        "script",
        "style",
        "noscript",
        "svg",
        "canvas",
        "iframe",
        "form",
    ]:
        for tag in soup.find_all(tag_name):
            tag.decompose()


def clean_external_text(
    value: str,
    *,
    maximum_characters: int = MAX_EXTRACTED_CHARACTERS,
) -> str:
    lines = []

    for line in str(value or "").splitlines():
        cleaned = " ".join(line.split())

        if cleaned:
            lines.append(cleaned)

    text = "\n".join(lines).strip()

    if len(text) > maximum_characters:
        text = text[:maximum_characters]

    return text


def extract_text_from_html(
    body: bytes,
) -> tuple[str, str]:
    soup = BeautifulSoup(body, "html.parser")

    title = ""

    if soup.title:
        title = clean_external_text(
            soup.title.get_text(" ", strip=True),
            maximum_characters=500,
        )

    _remove_unhelpful_html(soup)

    preferred_root = (
        soup.find("main")
        or soup.find("article")
        or soup.body
        or soup
    )

    text = clean_external_text(
        preferred_root.get_text("\n", strip=True)
    )

    if not text:
        raise ValueError(
            "No readable text was found on the HTML page."
        )

    return title, text


def _guess_filename(
    final_url: str,
    content_type: str,
) -> str:
    path_name = Path(urlparse(final_url).path).name

    if path_name:
        return path_name

    if content_type in PDF_CONTENT_TYPES:
        return "external_candidate.pdf"

    if content_type in TEXT_CONTENT_TYPES:
        return "external_candidate.txt"

    return "external_candidate.html"


def extract_text_from_pdf(
    body: bytes,
    final_url: str,
) -> tuple[str, str]:
    filename = _guess_filename(
        final_url,
        "application/pdf",
    )

    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"

    temporary_path: Path | None = None

    try:
        with NamedTemporaryFile(
            mode="wb",
            suffix=".pdf",
            delete=False,
        ) as temporary_file:
            temporary_file.write(body)
            temporary_path = Path(temporary_file.name)

        loaded = load_single_cv(temporary_path)
        text = clean_external_text(loaded.get("text", ""))

        if not text:
            raise ValueError(
                "The PDF did not contain readable text. It may "
                "be scanned or image-only."
            )

        return filename, text

    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink(missing_ok=True)


def extract_text_from_plain_text(
    body: bytes,
    final_url: str,
) -> tuple[str, str]:
    text = clean_external_text(
        body.decode("utf-8", errors="replace")
    )

    if not text:
        raise ValueError("The remote text file is empty.")

    return (
        _guess_filename(final_url, "text/plain"),
        text,
    )


def _detect_source_type(
    content_type: str,
    final_url: str,
    body: bytes,
) -> str:
    path = urlparse(final_url).path.lower()

    if (
        content_type in PDF_CONTENT_TYPES
        or path.endswith(".pdf")
        or body.startswith(b"%PDF")
    ):
        return "pdf"

    if (
        content_type in HTML_CONTENT_TYPES
        or path.endswith((".html", ".htm"))
        or b"<html" in body[:2048].lower()
    ):
        return "html"

    if (
        content_type in TEXT_CONTENT_TYPES
        or path.endswith((".txt", ".md", ".csv"))
    ):
        return "text"

    raise ValueError(
        "Unsupported remote content type. AIRS currently "
        "supports public HTML pages, PDF files, and text files."
    )


def extract_candidate_source_from_url(
    url: str,
) -> ExternalCandidateSource:
    downloaded = download_external_content(url)

    final_url = downloaded["final_url"]
    content_type = downloaded["content_type"]
    body = downloaded["body"]

    source_type = _detect_source_type(
        content_type,
        final_url,
        body,
    )

    if source_type == "html":
        title, text = extract_text_from_html(body)
    elif source_type == "pdf":
        title, text = extract_text_from_pdf(body, final_url)
    else:
        title, text = extract_text_from_plain_text(
            body,
            final_url,
        )

    return ExternalCandidateSource(
        source_url=str(url).strip(),
        final_url=final_url,
        source_type=source_type,
        title=title or _guess_filename(
            final_url,
            content_type,
        ),
        content_type=content_type,
        text=text,
        downloaded_bytes=int(
            downloaded["downloaded_bytes"]
        ),
    )