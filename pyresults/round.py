from pyresults.race_result import RaceResult
import os


class Round:
    def __init__(self, round_number):
        self.round_number = round_number
        self.race_result_paths: list[str] = self.get_race_result_paths()
        self.race_results : list[RaceResult] = self.get_race_results()

    def get_race_result_paths(self) -> list[str]:
        files = os.listdir(f"./input_data/{self.round_number}")
        return files
    
    def get_race_results(self) -> list[RaceResult]:
        return [RaceResult(path) for path in self.race_result_paths]
