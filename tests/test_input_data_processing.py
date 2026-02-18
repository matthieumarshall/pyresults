import types

import pandas as pd

from pyresults.config import build_default_config
from pyresults.results_processor import ResultsProcessor

_SAMPLE_INPUT = """Name,Club,Race No,Pos,Time,Gender,Category
Alice Smith,Club A,101,1,00:08:00,Male,U13 Boys
Bob Jones,Club B,102,2,00:08:30,Male,U13 Boys
"""


def test_results_processor_reads_input_data(tmp_path, monkeypatch) -> None:
    config = build_default_config()
    config.data_base_path = tmp_path / "data"

    processor = ResultsProcessor(config=config)
    processor._process_team_scores_for_race = types.MethodType(
        lambda self, race_result: None, processor
    )

    input_dir = tmp_path / "input_data" / "r1"
    input_dir.mkdir(parents=True)

    input_file = input_dir / "U13.csv"
    input_file.write_text(_SAMPLE_INPUT, encoding="utf-16")

    monkeypatch.chdir(tmp_path)
    processor._process_round("r1")

    output_file = config.data_base_path / "r1" / "U13.csv"
    assert output_file.exists()

    df = pd.read_csv(output_file)
    assert df["Name"].tolist() == ["Alice Smith", "Bob Jones"]
    assert df["Category"].iloc[0] == "U13B"
    assert df["Category"].nunique() == 1
