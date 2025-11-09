"""Generates standings for Oxon XC League 2024/25 season.
"""
from pyresults.results import Results
from argparse import ArgumentParser


if __name__ == "__main__":
    parser = ArgumentParser(description="Generates standings for Oxon XC League 2024/25 season.")
    parser.add_argument("--rounds", nargs="+", default=["r1", "r2", "r3", "r4", "r5"],
                        help="List of rounds to process (e.g. --rounds r1 r2 r3)")
    parser.add_argument("--excel", default=True, help="Generate Excel output")
    parser.add_argument("--pdf", default=True, help="Generate pdf output")
    args = parser.parse_args()
    
    Results.process(
        rounds_to_process=args.rounds,
        create_excel_=args.excel,
        create_pdf_=args.pdf
    )
