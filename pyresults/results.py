from pyresults.round import Round
from pyresults.create_excel import create_excel
from pyresults.create_pdf import create_pdf
from pyresults.config import CATEGORIES, RACE_MAPPINGS
from concurrent.futures import ThreadPoolExecutor
import os
import pandas as pd

class Publisher:
    @staticmethod
    def publish_results(
        create_excel_: bool,
        create_pdf_: bool
    ):
        if create_excel_:
            create_excel()
        if create_pdf_:
            create_pdf()
    

class Results:
    round_numbers = ["r1", "r2", "r3", "r4", "r5"]

    @classmethod
    def process(
        cls,
        rounds_to_process: list[str],
        create_excel_: bool,
        create_pdf_: bool
    ):
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(Round, round_to_process) for round_to_process in rounds_to_process
            ]
            for future in futures:
                future.result()
        cls.update_individual_scores()
        cls.update_overall_scores()
        cls.update_team_scores()
        Publisher.publish_results(create_excel_, create_pdf_)

    @classmethod
    def update_individual_scores(cls):
        for category in CATEGORIES:
            cls.update_individual_score(category)

    @classmethod
    def update_individual_score(cls, category):
        scores_path = f"./data/scores/{category}.csv"
        if not os.path.exists(scores_path):
            pd.DataFrame(
                columns=["Name", "Club"] + cls.round_numbers + ["score"]).to_csv(scores_path,
                index=False
            )
        scores_df = pd.read_csv(scores_path)
        rounds_to_count = 0
        category_race_name = RACE_MAPPINGS[category]
        for round_number in cls.round_numbers:
            round_result_path = f"./data/{round_number}/{category_race_name}.csv"
            round_result_exists = os.path.exists(round_result_path)
            if not round_result_exists:
                continue
            rounds_to_count += 1
            round_result = pd.read_csv(round_result_path)
            # Filter round_result to only include entries for the current category
            round_result = round_result[round_result['Category'] == category]
            scores_df = cls.populate_scores_in_df(scores_df, round_result, round_number)

        scores_df["score"] = scores_df.apply(cls.calculate_score, axis=1, args=(rounds_to_count - 1,))
        scores_df = scores_df.sort_values(by="score", ascending=True)
        # replace all values in column score that are greater than 99999 with empty string
        scores_df["score"] = scores_df["score"].apply(lambda x: "" if x > 99999 else x)
        scores_df.to_csv(scores_path, index=False)

    @classmethod
    def update_overall_scores(cls):
        scores_path = "./data/scores/MensOverall.csv"
        if not os.path.exists(scores_path):
            pd.DataFrame(
                columns=["Name", "Club"] + cls.round_numbers + ["score"]).to_csv(scores_path,
                index=False
            )
        scores_df = pd.read_csv(scores_path)
        rounds_to_count = 0
        category_race_name = "Men"
        for round_number in cls.round_numbers:
            round_result_path = f"./data/{round_number}/{category_race_name}.csv"
            round_result_exists = os.path.exists(round_result_path)
            if not round_result_exists:
                continue
            rounds_to_count += 1
            round_result = pd.read_csv(round_result_path)
            scores_df = cls.populate_scores_in_df(scores_df, round_result, round_number, position_column="Gen Pos")

        scores_df["score"] = scores_df.apply(cls.calculate_score, axis=1, args=(rounds_to_count - 1,))
        scores_df = scores_df.sort_values(by="score", ascending=True)
        # replace all values in column score that are greater than 99999 with empty string
        scores_df["score"] = scores_df["score"].apply(lambda x: "" if x > 99999 else x)
        scores_df.to_csv(scores_path, index=False)

        scores_path = "./data/scores/WomensOverall.csv"
        if not os.path.exists(scores_path):
            pd.DataFrame(
                columns=["Name", "Club"] + cls.round_numbers + ["score"]).to_csv(scores_path,
                index=False
            )
        scores_df = pd.read_csv(scores_path)
        rounds_to_count = 0
        category_race_name = "Women"
        for round_number in cls.round_numbers:
            round_result_path = f"./data/{round_number}/{category_race_name}.csv"
            round_result_exists = os.path.exists(round_result_path)
            if not round_result_exists:
                continue
            rounds_to_count += 1
            round_result = pd.read_csv(round_result_path)
            scores_df = cls.populate_scores_in_df(scores_df, round_result, round_number, position_column="Gen Pos")

        scores_df["score"] = scores_df.apply(cls.calculate_score, axis=1, args=(rounds_to_count - 1,))
        scores_df = scores_df.sort_values(by="score", ascending=True)
        # replace all values in column score that are greater than 99999 with empty string
        scores_df["score"] = scores_df["score"].apply(lambda x: "" if x > 99999 else x)
        scores_df.to_csv(scores_path, index=False)


    @staticmethod
    def calculate_score(row, rounds_to_count=4):
        selection = [x for x in row.index if x.startswith("r")]
        scores = row[selection]
        scores = scores.astype(float).fillna(99999.0)
        scores = sorted(scores, reverse=False)
        total_score_sum = sum(scores[:rounds_to_count])
        return total_score_sum
    
    @classmethod
    def populate_scores_in_df(cls, scores_df, round_result, round_number, position_column="Cat Pos"):
        for _, result in round_result.iterrows():
            mask = (scores_df['Name'] == result['Name']) & (scores_df['Club'] == result['Club'])
            if not mask.any():
                # Add new athlete
                new_row = pd.Series({'Name': result['Name'], 'Club': result['Club']})
                scores_df = pd.concat([scores_df, pd.DataFrame([new_row])], ignore_index=True)
                mask = (scores_df['Name'] == result['Name']) & (scores_df['Club'] == result['Club'])

            # Update position for this round
            scores_df.loc[mask, round_number] = result[position_column]
        return scores_df

    @classmethod
    def update_team_scores(cls):
        for team_category in [
            "Men",
            "Women",
            "U9B",
            "U9G",
            "U11B",
            "U11G",
            "U13B",
            "U13G",
            "U15B",
            "U15G",
            "U17M",
            "U17W"
        ]:
            scores_path = f"./data/scores/{team_category}.csv"
            if not os.path.exists(scores_path):
                pd.DataFrame(
                    columns=["Team"] + cls.round_numbers + ["score"]).to_csv(scores_path,
                    index=False
                )

