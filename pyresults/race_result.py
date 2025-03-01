import pandas as pd
import math
from pandas import DataFrame
from pyresults.config import GUESTS
from pyresults.config import CATEGORY_MAPPINGS, GENDER_MAPPINGS
from datetime import timedelta
import os

class RaceResult:
    def __init__(self, result_file_path):
        self.result_file_path = result_file_path
        self.df: DataFrame = self.read_file_to_df()
        self.clean_names()
        self.race_name = result_file_path.split(".")[-2].split("/")[-1]
        self.round_num = result_file_path.split(".")[-2].split("/")[-2]
        
        if not os.path.exists(f"./data/{self.round_num}/teams"):
            os.makedirs(f"./data/{self.round_num}/teams")
        
        self.df["Race No"] = self.df["Race No"].astype(str)
        self.df['Pos'] = pd.to_numeric(self.df['Pos'], errors='coerce')
        self.df['Time'] = pd.to_timedelta(self.df['Time'])
        self.df = self.df[~self.df['Race No'].isin(GUESTS)]
        self.df = self.reset_positions(self.df)
        self.handle_exceptions()
        self.df["Category"] = self.df.apply(lambda row: self.map_category(row, self.race_name), axis=1)
        self.persist_results()
        self.produce_team_results()

    def read_file_to_df(self) -> DataFrame:
        try:
            df = pd.read_csv(self.result_file_path, encoding="utf-16")
            df['Race No']
        except KeyError:
            df = pd.read_csv(self.result_file_path, encoding="utf-16", sep="\t")
        return df

    @staticmethod
    def clean_name(name) -> str:
        return name.replace("(2C)", "").replace("÷", "ö").strip()
    
    def clean_names(self) -> None:
        self.df['Name'] = self.df['Name'].apply(self.clean_name)

    @staticmethod
    def reset_positions(df) -> DataFrame:
        df = df.sort_values(['Category', 'Pos', 'Time'])
        df['Cat Pos'] = df.groupby('Category').cumcount() + 1
        try:
            df = df.sort_values(['Pos', "Time"])
            df.reset_index(drop=True, inplace=True)
            df['Gen Pos'] = df.groupby('Gender').cumcount() + 1
            df['Pos'] = df.index + 1
        except KeyError:
            df = df.sort_values(['Pos', "Time"])
            df.reset_index(drop=True, inplace=True)
            if df[df['Category'].str.startswith("Senior")].empty:
                df['Gen Pos'] = df.groupby('Category').cumcount() + 1
            else:
                df['Gen Pos'] = df.index + 1
            df['Pos'] = df.index + 1
        return df
    
    def handle_exceptions(self) -> None:
        if self.race_name == "Women" and self.round_num == "r3":
            # remove Cicely Arthur was accidentally included
            self.df = self.df[self.df["Race No"] != "1006"]
        elif self.race_name == "Women" and self.round_num == "r4":
            # remove Becky Window was accidentally included
            self.df = self.df[self.df["Race No"] != "51"]
        elif self.race_name == "Men" and self.round_num == "r3":
            # add David Cantwell and Troy Southall
            # and Jan Rasmussen (position pending)
            # and Caspar Cumberland (position pending - 28th ?)
            self.df = self.insert_athlete_into_df(
                df=self.df, 
                athlete={"Pos": 51, "Race No": "596", "Name": "Troy Southall", "Time": timedelta(minutes=33, seconds=29), "Category": "Senior Men", "Club": "Headington RR", "Gender": "Male"},
                position=51
            )
            self.df = self.insert_athlete_into_df(
                df=self.df, 
                athlete={"Pos": 186, "Race No": "1606", "Name": "David Cantwell", "Time": timedelta(minutes=40, seconds=5), "Category": "V50", "Club": "Woodstock Harriers AC", "Gender": "Male"},
                position=186
            )
        elif self.race_name == "U11B" and self.round_num == "r3":
            # add Miles Game of Woodstock into 57th
            self.df = self.insert_athlete_into_df(
                df=self.df, 
                athlete={"Pos": 57, "Race No": "1620", "Name": "Miles Game", "Time": timedelta(minutes=8, seconds=59), "Category": "U11 Boys", "Club": "Woodstock Harriers AC", "Gender": "Male"},
                position=57
            )
    
    @classmethod
    def insert_athlete_into_df(cls, df, athlete, position):
        new_row_df = pd.DataFrame([athlete])
        insert_index = position - 1
        df = pd.concat([df.iloc[:insert_index], new_row_df, df.iloc[insert_index:]]).reset_index(drop=True)
        df = cls.reset_positions(df)
        return df
    
    @staticmethod
    def map_category(row, race_name: str = "") -> str:
        category = row['Category'].strip()
        
        # Determine gender once
        if "Gender" in row:
            gender = row['Gender'].strip()
        elif "boys" in category.lower():
            gender = "Male"
        elif "girls" in category.lower():
            gender = "Female"
        else:
            gender = GENDER_MAPPINGS.get(race_name, "")
        
        # Single dictionary lookup
        if gender is not None and isinstance(gender, str):
            try:
                return CATEGORY_MAPPINGS[(gender, category)]
            except KeyError:
                raise Exception(f"Error with getting category for {race_name= } {gender= } {category= }")
        else:
            raise Exception(f"Error with getting category for {race_name= } {gender= } {category= }")

    def persist_results(self) -> None:
        self.df.to_csv(f"./data/{self.round_num}/{self.race_name}.csv", index=False)

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
        team_scores_df.to_csv(f"./data/{round_num}/teams/{category}.csv", index=False)
