import argparse

from textbook_kb.pdf_parser import extract_pages


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect page-level text extracted from a PDF."
    )

    parser.add_argument(
        "pdf_path",
        help="Path to the PDF file.",
    )

    parser.add_argument(
        "--pages",
        type=int,
        default=3,
        help="Number of pages to preview.",
    )

    args = parser.parse_args()

    pages = extract_pages(args.pdf_path)

    print(f"\nTotal pages: {len(pages)}")

    for page in pages[: args.pages]:
        print("\n" + "=" * 70)
        print(f"Page: {page.page_number}")
        print(f"Source: {page.source_file}")
        print("=" * 70)

       

        print(page.text)


if __name__ == "__main__":
    main()