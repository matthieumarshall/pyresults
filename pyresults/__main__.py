"""Generates standings for Oxon XC League 2024/25 season.
"""
from pyresults.results import Results
from argparse import ArgumentParser

# import os
# import glob
# import math
# import pandas as pd
# from pyresults.utils import calculate_score, read_results
# from pyresults.create_pdf import create_pdf
# from pyresults.create_excel import create_excel
# from pyresults.CONFIG import CATEGORIES, MENS_DIVISIONS, WOMENS_DIVISIONS
# from pyresults.data_gathering import get_round_numbers, clear_and_reset_scores, get_round_results_paths

# pd.set_option('display.max_rows', None)
# pd.set_option('display.max_columns', None)
# pd.set_option('display.width', None)
# pd.set_option('display.max_colwidth', None)

# rounds = get_rounds()
# clear_and_reset_scores()

# # for round_ in rounds:
# #     round_.set_results_paths()
    
# #     round_results_paths = get_round_results_paths(round_number)
# #     for results_csv in round_results_paths:
# #         pass


# #     category_results = CATEGORIES + ["MensOverall", "WomensOverall"]
# #     for category in category_results:
# #         category_results_csv_path = f"./data/scores/{category}.csv"


# for r in round_numbers:
#     for category in CATEGORIES + ["MensOverall", "WomensOverall"]:
#         if not os.path.exists(f"./data/scores/{category}.csv"):
#             pd.DataFrame(columns=["Name", "Club"] + round_numbers + ["score"]).to_csv(f"./data/scores/{category}.csv", index=False)

#     for results_csv in glob.glob(f"./data/{r}/*.csv"):
#         df = read_results(results_csv)

#         # Process each category's scores
#         for category in CATEGORIES:
#             category_results = df[df['Category'] == category]
#             if len(category_results) == 0:
#                 continue
#             # Load existing scores
#             scores_path = f"./data/scores/{category}.csv"
#             scores_df = pd.read_csv(scores_path)

#             # Update scores with new results
#             for _, result in category_results.iterrows():
#                 mask = (scores_df['Name'] == result['Name']) & (scores_df['Club'] == result['Club'])
#                 if not mask.any():
#                     # Add new athlete
#                     new_row = pd.Series({'Name': result['Name'], 'Club': result['Club']})
#                     scores_df = pd.concat([scores_df, pd.DataFrame([new_row])], ignore_index=True)
#                     mask = (scores_df['Name'] == result['Name']) & (scores_df['Club'] == result['Club'])

#                 # Update position for this round
#                 scores_df.loc[mask, r] = result['Cat Pos']
#             scores_df.to_csv(scores_path, index=False)
        
#         if "Men" in results_csv:
#             scores_path = f"./data/scores/MensOverall.csv"
#             scores_df = pd.read_csv(scores_path)
#             for _, result in df.iterrows():
#                 mask = (scores_df['Name'] == result['Name']) & (scores_df['Club'] == result['Club'])
#                 if not mask.any():
#                     # Add new athlete
#                     new_row = pd.Series({'Name': result['Name'], 'Club': result['Club']})
#                     scores_df = pd.concat([scores_df, pd.DataFrame([new_row])], ignore_index=True)
#                     mask = (scores_df['Name'] == result['Name']) & (scores_df['Club'] == result['Club'])

#                 # Update position for this round
#                 scores_df.loc[mask, r] = result['Pos']
#             scores_df.to_csv(scores_path, index=False)
#         elif "Women" in results_csv:
#             scores_path = f"./data/scores/WomensOverall.csv"
#             scores_df = pd.read_csv(scores_path)
#             for _, result in df.iterrows():
#                 mask = (scores_df['Name'] == result['Name']) & (scores_df['Club'] == result['Club'])
#                 if not mask.any():
#                     # Add new athlete
#                     new_row = pd.Series({'Name': result['Name'], 'Club': result['Club']})
#                     scores_df = pd.concat([scores_df, pd.DataFrame([new_row])], ignore_index=True)
#                     mask = (scores_df['Name'] == result['Name']) & (scores_df['Club'] == result['Club'])

#                 # Update position for this round
#                 scores_df.loc[mask, r] = result['Pos']
#             scores_df.to_csv(scores_path, index=False)
#         else:
#             pass

# for category in CATEGORIES + ["MensOverall", "WomensOverall"]:
#     df = pd.read_csv(f"./data/scores/{category}.csv")
#     df["score"] = df.apply(calculate_score, axis=1, args=(len(round_numbers) - 1,))
#     df = df.sort_values(by="score", ascending=True)
#     # replace all values in column score that are greater than 99999 with empty string
#     df["score"] = df["score"].apply(lambda x: "" if x > 99999 else x)
#     if category in ["MensOverall", "WomensOverall"]:
#         df = df.head(10)
#     df.to_csv(f"./data/scores/{category}.csv", index=False)

# def calculate_teams(df, category, round_num, team_size = 3):
#     """Calculate junior team scores based on gender positions"""
#     # calculate penalty score as one plus last gender position
#     penalty_score = df['Gen Pos'].max() + 1
#     # Group by club and sort by gender position
#     teams = []
#     clubs = df['Club'].unique()
#     for club in clubs:
#         club_runners = df[df['Club'] == club].sort_values('Gen Pos')

#         # Create teams of 3
#         num_complete_teams = len(club_runners) // team_size
#         for team_num in range(num_complete_teams):
#             start_idx = team_num * team_size
#             team = club_runners.iloc[start_idx:start_idx + team_size]
#             team_score = team['Gen Pos'].sum()
#             teams.append({
#                 "club": club,
#                 'team': f"{club} {chr(65 + team_num)}",
#                 'score': team_score
#             })

#         # Handle incomplete teams
#         remaining_runners = len(club_runners) % team_size
#         if remaining_runners > 0:
#             start_idx = num_complete_teams * team_size
#             team = club_runners.iloc[start_idx:]

#             # Special case for A teams - allow if at least one runner
#             if num_complete_teams == 0:  # This is an A team
#                 team_score = team['Gen Pos'].sum() + penalty_score * (team_size - len(team))
#                 teams.append({
#                     "club": club,
#                     'team': f"{club} A",
#                     'score': team_score
#                 })
#             # For B, C teams etc - keep original logic
#             elif remaining_runners >= math.ceil(0.5 * team_size):
#                 team_score = team['Gen Pos'].sum() + penalty_score * (team_size - len(team))
#                 teams.append({
#                     "club": club,
#                     'team': f"{club} {chr(65 + num_complete_teams)}",
#                     'score': team_score
#                 })
#     teams.append(
#         {
#             "club": "penalty",
#             'team': "penalty",
#             'score': penalty_score * team_size
#         }
#     )
#     team_scores_df = pd.DataFrame(teams)
#     team_scores_df = team_scores_df.sort_values(by="score", ascending=True)
#     team_scores_df.to_csv(f"./data/{round_num}/teams/{category}.csv", index=False)

# for r in round_numbers:
#     os.makedirs(f"./data/{r}/teams/", exist_ok=True)
#     # Process Junior Teams
#     for race in ['U9', 'U13', 'U15']:
#         df = read_results(f"./data/{r}/{race}.csv")
#         boys_results = df[df['Category'] == f"{race}B"]
#         girls_results = df[df['Category'] == f"{race}G"]
#         calculate_teams(boys_results, f"{race}B", round_num=r)
#         calculate_teams(girls_results, f"{race}G", round_num=r)
#     for race in ["U11B", "U11G"]:
#         df = read_results(f"./data/{r}/{race}.csv")
#         calculate_teams(df, race, round_num=r)

#     df = read_results(f"./data/{r}/U17.csv")
#     boys_results = df[df['Category'] == "U17M"]
#     girls_results = df[df['Category'] == "U17W"]
#     calculate_teams(boys_results, "U17M", round_num=r)
#     calculate_teams(girls_results, "U17W", round_num=r)

#     # Process Senior Teams
#     df = read_results(f"./data/{r}/Men.csv")
#     calculate_teams(df, "SM", round_num=r, team_size=7)
#     df = read_results(f"./data/{r}/Women.csv")
#     calculate_teams(df, "SW", round_num=r, team_size=4)

# # Process team scores
# team_categories = [c.split(".")[-2].split("/")[-1] for c in glob.glob("./data/r1/teams/*.csv")]
# os.makedirs("./data/scores/teams/", exist_ok=True)
# for category in team_categories:
#     team_scores = pd.DataFrame(columns=["team"])
#     penalties = {}
#     for r in round_numbers:
#         df = pd.read_csv(f"./data/{r}/teams/{category}.csv")[['team', 'score']]
#         penalties[r] = df[df['team'] == 'penalty']['score'].iloc[0]
#         df = df[df['team'] != 'penalty']
#         df = df.rename(columns={'score': r})
#         team_scores = pd.merge(left=team_scores, right=df, on=["team"], how="outer")
#     team_scores["score"] = team_scores.iloc[:, 1:].sum(axis=1)
#     has_empty = team_scores[round_numbers].isna().any(axis=1)
#     team_scores.loc[has_empty, 'score'] = pd.NA
#     team_scores = team_scores.sort_values(by="score", ascending=True, na_position='last')
#     team_scores = team_scores.fillna("")


#     # add division column to team scores
#     if category == "SM":
#         team_scores["division"] = team_scores["team"].apply(lambda x: MENS_DIVISIONS.get(x, "3"))
#     if category == "SW":
#         team_scores["division"] = team_scores["team"].apply(lambda x: WOMENS_DIVISIONS.get(x, "3"))
#     team_scores.to_csv(f"./data/scores/teams/{category}.csv", index=False)

# create_excel()
# create_pdf()



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
