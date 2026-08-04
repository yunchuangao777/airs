from services.external_candidate_import_service import (
    extract_candidate_source_from_url,
)


def main() -> None:
    url = input(
        "Enter a public candidate or portfolio URL: "
    ).strip()

    source = extract_candidate_source_from_url(
        url
    )

    print("\nSource type:")
    print(source.source_type)

    print("\nFinal URL:")
    print(source.final_url)

    print("\nTitle:")
    print(source.title)

    print("\nDownloaded bytes:")
    print(source.downloaded_bytes)

    print("\nExtracted text preview:")
    print(source.text[:2000])


if __name__ == "__main__":
    main()