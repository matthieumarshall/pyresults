from pyresults.race_result import RaceResult
from pathlib import Path
import glob


class Round:
    def __init__(self, round_number):
        self.round_number = round_number
        self.race_result_paths: list[str] = self.get_race_result_paths()
        self.race_results : list[RaceResult] = self.get_race_results()
        # process each RaceResult explicitly so constructors have no hidden IO
        for rr in self.race_results:
            try:
                rr.process()
            except Exception:
                # keep processing other races even if one fails
                raise

    def get_race_result_paths(self) -> list[str]:
        base_dir = Path(__file__).parent.parent
        pattern = str(base_dir / "input_data" / self.round_number / "*.csv")
        files = [str(Path(f)) for f in glob.glob(pattern)]
        return files
    
    def get_race_results(self) -> list[RaceResult]:
        return [RaceResult(path) for path in self.race_result_paths]
