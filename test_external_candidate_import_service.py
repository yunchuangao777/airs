from __future__ import annotations

from services.external_candidate_import_service import (
    clean_external_text,
    extract_text_from_html,
    validate_external_url,
)


def assert_rejected(url: str) -> None:
    try:
        validate_external_url(url)
    except ValueError:
        return

    raise AssertionError(
        f"Unsafe URL was accepted: {url}"
    )


def main() -> None:
    print("=" * 70)
    print("External Candidate Import Service Test")
    print("=" * 70)

    assert_rejected("file:///etc/passwd")
    assert_rejected("ftp://example.com/file.txt")
    assert_rejected("http://localhost:8501")
    assert_rejected("http://127.0.0.1")
    assert_rejected("http://10.0.0.5")
    assert_rejected("http://192.168.1.10")
    assert_rejected("http://169.254.169.254/latest/meta-data")
    assert_rejected("http://[::1]")

    print("[PASSED] Unsafe URL examples were rejected.")

    html = b"""
    <html>
        <head>
            <title>Jane Smith Portfolio</title>
            <style>.hidden { display: none; }</style>
            <script>console.log('ignore me')</script>
        </head>
        <body>
            <nav>Home About Contact</nav>
            <main>
                <h1>Jane Smith</h1>
                <p>Senior Financial Analyst</p>
                <p>Skills: Python, SQL, Power BI</p>
                <p>Experience: 8 years</p>
            </main>
        </body>
    </html>
    """

    title, text = extract_text_from_html(html)

    assert title == "Jane Smith Portfolio"
    assert "Jane Smith" in text
    assert "Python, SQL, Power BI" in text
    assert "console.log" not in text
    assert ".hidden" not in text

    print("[PASSED] HTML title and readable text were extracted.")

    cleaned = clean_external_text(
        "  Alice   Chen  \n\n  CPA   Manager  "
    )

    assert cleaned == "Alice Chen\nCPA Manager"

    print("[PASSED] Extracted text was normalized.")

    print("=" * 70)
    print(
        "[PASSED] External candidate import service "
        "unit tests passed."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()