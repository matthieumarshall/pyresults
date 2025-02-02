import pandas as pd
import glob

def create_excel():

    # produce final Excel of results with one sheet per category and team scores
    individual_scores = glob.glob("./data/scores/*.csv")
    team_scores = glob.glob("./data/scores/teams/*.csv")

    # Create a Pandas Excel writer using openpyxl as the engine
    with pd.ExcelWriter('./data/OxfordshireCrossCountryLeagueStandings.xlsx', engine='openpyxl') as writer:
        for file in individual_scores:
            # Read each CSV file into a DataFrame
            df = pd.read_csv(file)

            # Extract the base name of the file to use as the sheet name
            sheet_name = file.split('.')[-2].split("/")[-1] + "_individual"  # Removes .csv extension
            if sheet_name in ["MensOverall_individual", "WomensOverall_individual"]:
                sheet_name += "_top_10"
            # Write the DataFrame to a specific sheet
            df.to_excel(writer, sheet_name=sheet_name, index=False)

        for file in team_scores:
            # Read each CSV file into a DataFrame
            df = pd.read_csv(file)

            # Extract the base name of the file to use as the sheet name
            sheet_name = file.split('.')[-2].split("/")[-1] + "_teams"
            if sheet_name == "SM_teams":
                sheet_name = "Mens_teams"
            elif sheet_name == "SW_teams":
                sheet_name = "Womens_teams"
            # Write the DataFrame to a specific sheet
            df.to_excel(writer, sheet_name=sheet_name, index=False)