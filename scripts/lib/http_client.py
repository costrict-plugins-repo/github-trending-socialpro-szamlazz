"""Minimal stdlib-only multipart/form-data HTTP client for szamlazz.hu.

No external dependencies — uses urllib.request + a hand-rolled
multipart body builder. This replaces the bash+curl wrappers from the
original skill and makes the plugin run natively on Windows.
"""
from __future__ import annotations

import secrets
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class HttpResponse:
    body: bytes
    headers: Dict[str, str]
    status: int


class SzamlazzHttpError(Exception):
    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


def build_multipart_body(
    fields: Dict[str, str],
    files: Dict[str, Tuple[str, bytes]],
) -> Tuple[bytes, str]:
    """Return (body_bytes, content_type_header).

    `fields` — regular form fields, name → value.
    `files`  — file fields, name → (filename, file_bytes).
    """
    boundary = "----socialpro" + secrets.token_hex(16)
    lines: list[bytes] = []

    for name, value in fields.items():
        lines.append(f"--{boundary}".encode("utf-8"))
        lines.append(f'Content-Disposition: form-data; name="{name}"'.encode("utf-8"))
        lines.append(b"")
        lines.append(value.encode("utf-8"))

    for name, (filename, content) in files.items():
        lines.append(f"--{boundary}".encode("utf-8"))
        lines.append(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"'.encode("utf-8")
        )
        lines.append(b"Content-Type: application/xml")
        lines.append(b"")
        lines.append(content)

    lines.append(f"--{boundary}--".encode("utf-8"))
    lines.append(b"")  # trailing CRLF

    body = b"\r\n".join(lines)
    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


def post_multipart(
    url: str,
    files: Dict[str, Tuple[str, bytes]],
    fields: Dict[str, str] | None = None,
    timeout: int = 60,
) -> HttpResponse:
    """POST a multipart/form-data request to `url`.

    Raises SzamlazzHttpError on network or HTTP errors.
    """
    fields = fields or {}
    body, content_type = build_multipart_body(fields, files)

    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": content_type,
            "Content-Length": str(len(body)),
            "User-Agent": "socialpro-szamlazz/1.0 (+https://github.com/socialproKGCMG/socialpro-szamlazz)",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return HttpResponse(
                body=resp.read(),
                headers=dict(resp.headers),
                status=resp.status,
            )
    except urllib.error.HTTPError as e:
        raise SzamlazzHttpError(
            f"HTTP {e.code} from {url}: {e.reason}", status_code=e.code
        ) from e
    except urllib.error.URLError as e:
        raise SzamlazzHttpError(f"Network error to {url}: {e.reason}") from e
