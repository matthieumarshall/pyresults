import pandas as pd
import math
from pandas import DataFrame
from pyresults.CONFIG import GUESTS
from datetime import timedelta
from pathlib import Path
from pyresults.utils import (
    clean_name,
    reset_positions,
    handle_exceptions,
    map_category,
)

class RaceResult:
    def __init__(self, result_file_path):
        self.result_file_path = Path(result_file_path)
        self.df: DataFrame = self.read_file_to_df()
        # normalize names
        self.df['Name'] = self.df['Name'].apply(clean_name)
        self.race_name = self.result_file_path.stem
        self.round_num = self.result_file_path.parent.name

        output_teams_dir = Path(__file__).parent.parent / "data" / self.round_num / "teams"
        output_teams_dir.mkdir(parents=True, exist_ok=True)

        self.df["Race No"] = self.df["Race No"].astype(str)
        self.df['Pos'] = pd.to_numeric(self.df['Pos'], errors='coerce')
        self.df['Time'] = pd.to_timedelta(self.df['Time'])
        self.df = self.df[~self.df['Race No'].isin(GUESTS)]
        self.df = reset_positions(self.df)
        # apply any race/round-specific exceptions
        self.df = handle_exceptions(self.df, self.race_name, self.round_num)
        self.df["Category"] = self.df.apply(lambda row: map_category(row, self.race_name), axis=1)

    def read_file_to_df(self) -> DataFrame:
        try:
            df = pd.read_csv(self.result_file_path, encoding="utf-16")
            df['Race No']
        except KeyError:
            df = pd.read_csv(self.result_file_path, encoding="utf-16", sep="\t")
        return df
    def process(self) -> None:
        """Persist results and generate team outputs.

        This is separated from __init__ so construction has no IO side-effects.
        """
        self.persist_results()
        self.produce_team_results()

    def persist_results(self) -> None:
        output_path = Path(__file__).parent.parent / "data" / self.round_num / f"{self.race_name}.csv"
        self.df.to_csv(output_path, index=False)

    def produce_team_results(self) -> None:
        team_races = {
            "U9": ("U9B", "U9G"),
            "Men": ("Men",),
            "Women": ("Women",),
            "U11B": ("U11B",),
            "U11G": ("U11G",),
            "U13": ("U13B", "U13G"),
            "U15": ("U15B", "U15G"),
            "U17": ("U17M", "U17W")
        }[self.race_name]
        team_size = {
            "Men": 7,
            "Women": 4,
            "U11B": 3,
            "U11G": 3,
            "U9": 3,
            "U13": 3,
            "U15": 3,
            "U17": 3
        }[self.race_name]
        for team_race in team_races:
            self.calculate_teams(
                df=self.df,
                category=team_race,
                round_num=self.round_num,
                team_size=team_size  
            )

    @staticmethod
    def calculate_teams(df, category, round_num, team_size = 3):
        """Calculate junior team scores based on gender positions"""
        if category in ["U9B", "U9G", "U13B", "U13G", "U15B", "U15G", "U17M", "U17W"]:
            # if category column is null, then filter on gender
            if not (df['Category'] == category).any():
                df = df[df["Gender"] == {"G":"Female", "B":"Male", "M": "Male", "W": "Female"}[category[-1]]]
            else:
                df = df[df['Category'] == category].sort_values('Gen Pos')
        # calculate penalty score as one plus last gender position
        penalty_score = df['Gen Pos'].max() + 1
        # Group by club and sort by gender position
        teams = []
        clubs = df['Club'].unique()
        for club in clubs:
            club_runners = df[df['Club'] == club].sort_values('Gen Pos')
            # Create teams of 3
            num_complete_teams = len(club_runners) // team_size
            for team_num in range(num_complete_teams):
                start_idx = team_num * team_size
                team = club_runners.iloc[start_idx:start_idx + team_size]
                team_score = team['Gen Pos'].sum()
                teams.append({
                    "club": club,
                    'team': f"{club} {chr(65 + team_num)}",
                    'score': team_score
                })

            # Handle incomplete teams
            remaining_runners = len(club_runners) % team_size
            if remaining_runners > 0:
                start_idx = num_complete_teams * team_size
                team = club_runners.iloc[start_idx:]

                # Special case for A teams - allow if at least one runner
                if num_complete_teams == 0:  # This is an A team
                    team_score = team['Gen Pos'].sum() + penalty_score * (team_size - len(team))
                    teams.append({
                        "club": club,
                        'team': f"{club} A",
                        'score': team_score
                    })
                # For B, C teams etc - keep original logic
                elif remaining_runners >= math.ceil(0.5 * team_size):
                    team_score = team['Gen Pos'].sum() + penalty_score * (team_size - len(team))
                    teams.append({
                        "club": club,
                        'team': f"{club} {chr(65 + num_complete_teams)}",
                        'score': team_score
                    })
        teams.append(
            {
                "club": "penalty",
                'team': "penalty",
                'score': penalty_score * team_size
            }
        )
        team_scores_df = pd.DataFrame(teams)
        team_scores_df = team_scores_df.sort_values(by="score", ascending=True)
        output_path = Path(__file__).parent.parent / "data" / round_num / "teams" / f"{category}.csv"
        team_scores_df.to_csv(output_path, index=False)
