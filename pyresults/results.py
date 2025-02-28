from pyresults.round import Round
from pyresults.create_excel import create_excel
from pyresults.create_pdf import create_pdf
from pyresults.CONFIG import CATEGORIES
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
        for round_to_process in rounds_to_process:
            Round(round_to_process)
        cls.update_scores()
        Publisher.publish_results(create_excel_, create_pdf_)

    @classmethod
    def update_scores(cls):
        for category in CATEGORIES:
            cls.update_score(category)

    @classmethod
    def update_score(cls, category):
        scores_path = f"./data/scores/{category}.csv"
        if not os.path.exists(scores_path):
            pd.DataFrame(
                columns=["Name", "Club"] + cls.round_numbers + ["score"]).to_csv(scores_path,
                index=False
            )
        scores_df = pd.read_csv(scores_path)
        rounds_to_count = 0
        for round_number in cls.round_numbers:
            round_result_exists = os.path.exists(f"./data/{round_number}/{category}.csv")
            if not round_result_exists:
                continue
            rounds_to_count += 1
            round_result = pd.read_csv(f"./data/{round_number}/{category}.csv")
            scores_df = cls.populate_scores_in_df(scores_df, round_result, round_number)


            if "Men" in category:
                scores_path = "./data/scores/MensOverall.csv"
                if not os.path.exists(scores_path):
                    pd.DataFrame(
                        columns=["Name", "Club"] + cls.round_numbers + ["score"]).to_csv(scores_path,
                        index=False
                    )
                scores_df = pd.read_csv(scores_path)
                for _, result in round_result.iterrows():
                    mask = (scores_df['Name'] == result['Name']) & (scores_df['Club'] == result['Club'])
                    if not mask.any():
                        # Add new athlete
                        new_row = pd.Series({'Name': result['Name'], 'Club': result['Club']})
                        scores_df = pd.concat([scores_df, pd.DataFrame([new_row])], ignore_index=True)
                        mask = (scores_df['Name'] == result['Name']) & (scores_df['Club'] == result['Club'])

                    # Update position for this round
                    scores_df.loc[mask, round_number] = result['Pos']
                scores_df.to_csv(scores_path, index=False)
            elif "Women" in category:
                scores_path = "./data/scores/WomensOverall.csv"
                if not os.path.exists(scores_path):
                    pd.DataFrame(
                        columns=["Name", "Club"] + cls.round_numbers + ["score"]).to_csv(scores_path,
                        index=False
                    )
                scores_df = pd.read_csv(scores_path)
                for _, result in round_result.iterrows():
                    mask = (scores_df['Name'] == result['Name']) & (scores_df['Club'] == result['Club'])
                    if not mask.any():
                        # Add new athlete
                        new_row = pd.Series({'Name': result['Name'], 'Club': result['Club']})
                        scores_df = pd.concat([scores_df, pd.DataFrame([new_row])], ignore_index=True)
                        mask = (scores_df['Name'] == result['Name']) & (scores_df['Club'] == result['Club'])

                    # Update position for this round
                    scores_df.loc[mask, round_number] = result['Pos']
                scores_df.to_csv(scores_path, index=False)
            else:
                pass

        scores_df["score"] = scores_df.apply(cls.calculate_score, axis=1, args=(rounds_to_count,))
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
    def populate_scores_in_df(cls, scores_df, round_result, round_number):
        for _, result in round_result.iterrows():
            mask = (scores_df['Name'] == result['Name']) & (scores_df['Club'] == result['Club'])
            if not mask.any():
                # Add new athlete
                new_row = pd.Series({'Name': result['Name'], 'Club': result['Club']})
                scores_df = pd.concat([scores_df, pd.DataFrame([new_row])], ignore_index=True)
                mask = (scores_df['Name'] == result['Name']) & (scores_df['Club'] == result['Club'])

            # Update position for this round
            scores_df.loc[mask, round_number] = result['Pos']
        return scores_df