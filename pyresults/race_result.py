import pandas as pd
from pandas import DataFrame
from pyresults.CONFIG import GUESTS
from pyresults.CONFIG import CATEGORY_MAPPINGS, GENDER_MAPPINGS
from datetime import timedelta

class RaceResult:
    def __init__(self, result_file_path):
        self.result_file_path = result_file_path
        self.df: DataFrame = self.read_file_to_df()
        self.clean_names()

        self.race_name = result_file_path.split(".")[-2].split("/")[-1]
        self.round_num = result_file_path.split(".")[-2].split("/")[-2]
        self.df["Race No"] = self.df["Race No"].astype(str)
        self.df['Pos'] = pd.to_numeric(self.df['Pos'], errors='coerce')
        self.df['Time'] = pd.to_timedelta(self.df['Time'])
        self.df = self.df[~self.df['Race No'].isin(GUESTS)]
        self.df = self.reset_positions(self.df)
        self.handle_exceptions()
        self.df["Category"] = self.df.apply(self.map_category, axis=1)
        self.persist_results()

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
            return CATEGORY_MAPPINGS.get((gender, category), "")
        return ""

    def persist_results(self) -> None:
        self.df.to_csv(f"./data/{self.round_num}/{self.race_name}.csv", index=False)
