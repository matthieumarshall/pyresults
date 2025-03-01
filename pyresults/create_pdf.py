from fpdf import FPDF
import pandas as pd
from datetime import datetime

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.font_size = 11  # Slightly larger base font

    def header(self):
        # Remove title from header - it will be blank
        pass

    def add_title(self):
        # Add this new method
        self.add_page()
        self.set_font('Arial', 'B', 16)  # Bigger font for main title
        self.cell(0, 10, 'Oxfordshire Cross Country League Standings 2024-25', 0, 1, 'C')
        self.ln(1)  # Add some space after title

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        
        # Calculate width for each section
        page_width = self.w - 2 * self.l_margin
        section_width = page_width / 3
        
        # Left - League name
        self.cell(section_width, 10, 'Oxfordshire Cross Country League Standings', 0, 0, 'L')
        
        # Center - Page number
        self.cell(section_width, 10, f'Page {self.page_no()}', 0, 0, 'C')
        
        # Right - Date
        current_date = datetime.now().strftime("%d/%m/%Y")
        self.cell(section_width, 10, current_date, 0, 0, 'R')

    def will_table_fit(self, df, row_height):
        # Calculate total height needed
        total_rows = len(df) + 1  # Add 1 for header
        table_height = total_rows * row_height
        # Get remaining space on page
        space_remaining = self.h - self.get_y() - self.b_margin
        return table_height <= space_remaining

    def add_table(self, title, df, first_page=False, string_columns=[1,2]):
        # In your existing code, before setting font:
        if first_page:
            self.ln(1)
        elif not self.will_table_fit(df, self.font_size + 2):
            self.add_page()
        else:
            # Add some spacing between tables if we're not on a new page
            self.ln(10)  # 10mm gap between tables
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, title, 0, 1, 'C')
        self.ln(10)

        self.set_font('Arial', 'B', 12)
        page_width = self.w - 2 * self.l_margin 
        # Calculate widths for first string columns
        col_widths = []
        for i in string_columns:
            if i < len(df.columns):
                # Get max width of column header and data
                header_width = self.get_string_width(str(df.columns[i])) + 4  # Add padding
                data_width = max([1] + [self.get_string_width(str(x)) for x in df[df.columns[i]] if pd.notnull(x)]) + 4
                col_widths.append(max(header_width, data_width))
        
        # Calculate remaining width and divide among other columns
        remaining_width = page_width - sum(col_widths)
        remaining_cols = len(df.columns) - len(string_columns)
        if remaining_cols > 0:
            standard_col_width = remaining_width / remaining_cols
            col_widths.extend([standard_col_width] * remaining_cols)
            col_widths = [standard_col_width] + col_widths  # Update first column width
        
        row_height = self.font_size + 2

        # Header
        self.set_font('Arial', 'B', 12)
        for i, column in enumerate(df.columns):
            self.cell(col_widths[i], row_height, column, 1, 0, 'C')
        self.ln(row_height)

        # Data
        self.set_font('Arial', '', 12)
        for _, row in df.iterrows():
            for i, cell in enumerate(row):
                if title in ("Mens Teams", "Womens Teams") and row['Pos'] in [1,2] and row['division'] in [2,3]:
                    self.set_fill_color(144, 238, 144)
                    self.cell(col_widths[i], row_height, str(cell), 1, 0, 'C', 1)
                elif title in ("Mens Teams", "Womens Teams")and row['Pos'] in [9,10] and row['division'] in [1,2]:
                    self.set_fill_color(255, 182, 193)
                    self.cell(col_widths[i], row_height, str(cell), 1, 0, 'C', 1)
                else:
                    self.cell(col_widths[i], row_height, str(cell), 1, 0, 'C')
            self.ln(row_height)

def create_pdf():
    # Create a PDF instance
    pdf = PDF()
    pdf.add_title()

    tables_to_add = [
        './data/scores/U9G.csv',
        './data/scores/teams/U9G.csv',
        './data/scores/U9B.csv',
        './data/scores/teams/U9B.csv',
        './data/scores/U11G.csv',
        './data/scores/teams/U11G.csv',
        './data/scores/U11B.csv',
        './data/scores/teams/U11B.csv',
        './data/scores/U13G.csv',
        './data/scores/teams/U13G.csv',
        './data/scores/U13B.csv',
        './data/scores/teams/U13B.csv',
        './data/scores/U15G.csv',
        './data/scores/teams/U15G.csv',
        './data/scores/U15B.csv',
        './data/scores/teams/U15B.csv',
        './data/scores/U17W.csv',
        './data/scores/teams/U17W.csv',
        './data/scores/U17M.csv',
        './data/scores/teams/U17M.csv',
        './data/scores/U20W.csv',
        './data/scores/U20M.csv',
        './data/scores/SW.csv',
        './data/scores/WV40.csv',
        './data/scores/WV50.csv',
        './data/scores/WV60.csv',
        './data/scores/WV70.csv',
        './data/scores/teams/Women.csv',
        './data/scores/SM.csv',
        './data/scores/MV40.csv',
        './data/scores/MV50.csv',
        './data/scores/MV60.csv',
        './data/scores/MV70.csv',
        './data/scores/teams/Men.csv',
        './data/scores/WomensOverall.csv',
        './data/scores/MensOverall.csv',
    ]

    for table_no, standings_csv in enumerate(tables_to_add):
        suffix = "Teams" if "teams" in standings_csv else "Individuals"

        df = pd.read_csv(standings_csv)
        df.insert(0, 'Pos', range(1, len(df) + 1))
        # Convert race columns to integers, keeping empty strings for nulls
        race_cols = [col for col in df.columns if col.startswith('r') and col[1:].isdigit()]
        for col in race_cols + ["score"]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].apply(lambda x: int(x) if pd.notnull(x) else "")

        category = standings_csv.split("/")[-1].split(".")[0]
        category = category.replace("MV", "Mens Vet").replace("WV", "Womens Vet")
        if category == "Men" and suffix == "Individuals":
            category = "Senior Men"
        if category == "Men" and suffix == "Teams":
            category = "Mens"
            df = df.sort_values(['division', 'score'])
            df['Pos'] = df.groupby('division').cumcount() + 1
        elif category == "Women" and suffix == "Individuals":
            category = "Senior Women"
        elif category == "Women" and suffix == "Teams":
            category = "Womens"
            df = df.sort_values(['division', 'score'])
            df['Pos'] = df.groupby('division').cumcount() + 1
        elif category.endswith("B"):
            category = f"{category[:-1]} Boys"
        elif category.endswith("G"):
            category = f"{category[:-1]} Girls"
        elif category == "SW":
            category = "Senior Womens"
        elif category == "SM":
            category = "Senior Mens"
        elif category.endswith("M"):
            category = f"{category[:-1]} Men"
        elif category.endswith("W"):
            category = f"{category[:-1]} Women"
        elif category.endswith("Overall"):
            gender = category.split("Overall")[0]
            category = f"{gender} Overall"
            suffix = ""
        pdf.add_table(f"{category} {suffix}", df, first_page=table_no == 0, string_columns=[1] if "teams" in standings_csv else [1,2])

    # Save the PDF
    pdf.output("./data/OxfordshireCrossCountryLeagueStandings.pdf")

if __name__ == "__main__":
    create_pdf()
