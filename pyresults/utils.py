from datetime import timedelta
import pandas as pd
from pyresults.CONFIG import CATEGORY_MAPPINGS, GENDER_MAPPINGS

GUESTS = ["1635", "1636", "956", "1652"] + [str(x) for x in range(1718, 1764)]

# Define constants outside function
GENDER_MAPPINGS = {
    "Men": "Male",
    "U11B": "Male",
    "U11G": "Female",
    "Women": "Female"
}

CATEGORY_MAPPINGS = {
    ("Male", "Senior Men"): "SM",
    ("Male", "U20 Men"): "U20M",
    ("Male", "V40"): "MV40",
    ("Male", "V50"): "MV50",
    ("Male", "V60"): "MV60",
    ("Male", "V70+"): "MV70",
    ("Female", "Senior Women"): "SW",
    ("Female", "U20 Women"): "U20W",
    ("Female", "V40"): "WV40",
    ("Female", "V50"): "WV50",
    ("Female", "V60"): "WV60",
    ("Female", "V70+"): "WV70",
    ("Male", "U9 Boys"): "U9B",
    ("Female", "U9 Girls"): "U9G",
    ("Male", "U11 Boys"): "U11B",
    ("Female", "U11 Girls"): "U11G",
    ("Male", "U13 Boys"): "U13B",
    ("Female", "U13 Girls"): "U13G",
    ("Male", "U13B"): "U13B",
    ("Female", "U13G"): "U13G",
    ("Male", "U15 Boys"): "U15B",
    ("Female", "U15 Girls"): "U15G",
    ("Male", "U17 Boys"): "U17M",
    ("Female", "U17 Girls"): "U17W",
}

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
        gender = GENDER_MAPPINGS.get(race_name)
    
    # Single dictionary lookup
    return CATEGORY_MAPPINGS.get((gender, category))


def calculate_score(row, rounds_to_count=4):
    selection = [x for x in row.index if x.startswith("r")]
    scores = row[selection]
    scores = scores.astype(float).fillna(99999.0)
    scores = sorted(scores, reverse=False)
    total_score_sum = sum(scores[:rounds_to_count])
    return total_score_sum

def read_results(path):

    def clean_name(name) -> str:
        return name.replace("(2C)", "").replace("÷", "ö").strip()

    try:
        df = pd.read_csv(path, encoding="utf-16")
        df['Race No']
    except KeyError:
        df = pd.read_csv(path, encoding="utf-16", sep="\t")
    # Clean names by removing (2C)
    df['Name'] = df['Name'].apply(clean_name)

    race_name = path.split(".")[-2].split("/")[-1]
    round_num = path.split(".")[-2].split("/")[-2]
    df["Race No"] = df["Race No"].astype(str)
    df['Pos'] = pd.to_numeric(df['Pos'], errors='coerce')
    df['Time'] = pd.to_timedelta(df['Time'])
    df = df[~df['Race No'].isin(GUESTS)]
    df = reset_positions(df)
    df = handle_exceptions(df, race_name, round_num)
    df["Category"] = df.apply(lambda x: map_category(x, race_name), axis=1)
    return df

def insert_athlete_into_df(df, athlete, position):
    new_row_df = pd.DataFrame([athlete])
    insert_index = position - 1
    df = pd.concat([df.iloc[:insert_index], new_row_df, df.iloc[insert_index:]]).reset_index(drop=True)
    df = reset_positions(df)
    return df

def handle_exceptions(df, race_name, round_num):
    if race_name == "Women" and round_num == "r3":
        # remove Cicely Arthur was accidentally included
        df = df[df["Race No"] != "1006"]
    elif race_name == "Women" and round_num == "r4":
        # remove Becky Window was accidentally included
        df = df[df["Race No"] != "51"]
    elif race_name == "Men" and round_num == "r3":
        # add David Cantwell and Troy Southall
        # and Jan Rasmussen (position pending)
        # and Caspar Cumberland (position pending - 28th ?)
        df = insert_athlete_into_df(
            df=df, 
            athlete={"Pos": 51, "Race No": "596", "Name": "Troy Southall", "Time": timedelta(minutes=33, seconds=29), "Category": "Senior Men", "Club": "Headington RR", "Gender": "Male"},
            position=51
        )
        df = insert_athlete_into_df(
            df=df, 
            athlete={"Pos": 186, "Race No": "1606", "Name": "David Cantwell", "Time": timedelta(minutes=40, seconds=5), "Category": "V50", "Club": "Woodstock Harriers AC", "Gender": "Male"},
            position=186
        )
    elif race_name == "U11B" and round_num == "r3":
        # add Miles Game of Woodstock into 57th
        df = insert_athlete_into_df(
            df=df, 
            athlete={"Pos": 57, "Race No": "1620", "Name": "Miles Game", "Time": timedelta(minutes=8, seconds=59), "Category": "U11 Boys", "Club": "Woodstock Harriers AC", "Gender": "Male"},
            position=57
        )
    return df

def reset_positions(df):
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
