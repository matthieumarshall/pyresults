import glob
import shutil
import os
from pyresults.round import Round

def get_round_numbers() -> list[Round]:
    rounds = glob.glob("./data/r*")
    round_numbers = [r.split("/")[-1] for r in rounds]
    rounds = [Round(round_number) for round_number in round_numbers]
    return rounds

def clear_and_reset_scores() -> None:
    shutil.rmtree("./data/scores/", ignore_errors=True)
    os.makedirs("./data/scores/")

def get_round_results_paths(round_number: str) -> list[str]:
    return glob.glob(f"./data/{round_number}/*.csv")