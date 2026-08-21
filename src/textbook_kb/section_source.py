def select_section_pages(
    pages: list[ParsedPage],
    metadata: SectionMetadata,
) -> list[ParsedPage]:
    """Select parsed pages that belong to a textbook section."""

    section_pages = [
        page
        for page in pages
        if metadata.page_start <= page.page_number <= metadata.page_end
    ]

    expected_page_numbers = set(
        range(metadata.page_start, metadata.page_end + 1)
    )

    actual_page_numbers = {
        page.page_number
        for page in section_pages
    }

    missing_page_numbers = expected_page_numbers - actual_page_numbers

    if missing_page_numbers:
        missing = sorted(missing_page_numbers)

        raise ValueError(
            f"Missing parsed pages for section "
            f"{metadata.section}: {missing}"
        )

    return section_pages