"""Competition configuration module.

Provides the main configuration class that encapsulates all competition
settings, replacing hard-coded constants.
"""

from pathlib import Path

from .category_config import CategoryConfig, build_default_categories


class CompetitionConfig:
    """Main configuration class for the competition.

    This class encapsulates all configuration settings, allowing them to be
    injected into services and repositories. This follows the Dependency
    Inversion Principle and makes the system testable and configurable.
    """

    def __init__(
        self,
        category_config: CategoryConfig,
        guest_numbers: set[str],
        round_numbers: list[str],
        data_base_path: Path,
        mens_divisions: dict[str, str],
        womens_divisions: dict[str, str],
        gender_mappings: dict[str, str],
        category_mappings: dict[tuple[str, str], str],
    ):
        """Initialize competition configuration.

        Args:
            category_config: Category configuration
            guest_numbers: Set of race numbers for guest athletes
            round_numbers: List of round identifiers (e.g., ["r1", "r2", ...])
            data_base_path: Base path for data files
            mens_divisions: Mapping of club names to division numbers for men
            womens_divisions: Mapping of club names to division numbers for women
            gender_mappings: Mapping of race names to genders
            category_mappings: Mapping of (gender, race_category) to category codes
        """
        self.category_config = category_config
        self.guest_numbers = guest_numbers
        self.round_numbers = round_numbers
        self.data_base_path = data_base_path
        self.mens_divisions = mens_divisions
        self.womens_divisions = womens_divisions
        self.gender_mappings = gender_mappings
        self.category_mappings = category_mappings

    def is_guest(self, race_number: str) -> bool:
        """Check if a race number belongs to a guest athlete.

        Args:
            race_number: Race number to check

        Returns:
            True if race number is a guest, False otherwise
        """
        return race_number in self.guest_numbers

    def get_division(self, club: str, gender: str) -> str:
        """Get the division number for a club.

        Args:
            club: Club name
            gender: "Male" or "Female"

        Returns:
            Division number as string, "3" if not found in divisions 1-2
        """
        divisions = self.mens_divisions if gender == "Male" else self.womens_divisions
        return divisions.get(club, "3")

    def map_category(self, gender: str, race_category: str) -> str:
        """Map a race category to a standard category code.

        Args:
            gender: Athlete gender
            race_category: Category from race results

        Returns:
            Standard category code (e.g., "U13B", "MV40")

        Raises:
            ValueError: If mapping not found
        """
        key = (gender, race_category)
        if key not in self.category_mappings:
            raise ValueError(f"No category mapping for {key}")
        return self.category_mappings[key]

    def get_gender_for_race(self, race_name: str) -> str:
        """Get the gender for a race name.

        Args:
            race_name: Name of the race (e.g., "Men", "U11B")

        Returns:
            Gender string ("Male" or "Female")

        Raises:
            ValueError: If race name not in mappings
        """
        if race_name not in self.gender_mappings:
            raise ValueError(f"No gender mapping for race: {race_name}")
        return self.gender_mappings[race_name]


def build_default_config() -> CompetitionConfig:
    """Build the default Oxfordshire XC League configuration.

    This function constructs the configuration matching the original
    hard-coded values in CONFIG.py.

    Returns:
        CompetitionConfig with default settings
    """
    # Guest numbers
    guests = {"1635", "1636", "956", "1652"} | {str(x) for x in range(1718, 1764)}

    # Round numbers
    round_numbers = ["r1", "r2", "r3", "r4", "r5"]

    # Base path for data
    data_base_path = Path("./data")

    # Men's divisions
    mens_divisions = {
        "Abingdon AC A": "1",
        "Swindon Harriers A": "1",
        "Oxford City AC A": "1",
        "Headington RR A": "1",
        "Witney Road Runners A": "1",
        "Newbury AC A": "1",
        "White Horse Harriers A": "1",
        "Alchester Running Club A": "1",
        "Didcot Runners A": "1",
        "Swindon Harriers B": "1",
        "Abingdon AC B": "2",
        "Witney Road Runners B": "2",
        "Newbury AC B": "2",
        "Headington RR B": "2",
        "Woodstock Harriers AC A": "2",
        "Eynsham Road Runners A": "2",
        "Harwell Harriers A": "2",
        "White Horse Harriers B": "2",
        "Oxford Tri A": "2",
        "Radley Athletic Club A": "2",
    }

    # Women's divisions
    womens_divisions = {
        "Headington RR A": "1",
        "Oxford City AC A": "1",
        "Swindon Harriers A": "1",
        "Abingdon AC A": "1",
        "Newbury AC A": "1",
        "Headington RR B": "1",
        "White Horse Harriers A": "1",
        "Witney Road Runners A": "1",
        "Headington RR C": "1",
        "Didcot Runners A": "1",
        "Banbury harriers AC A": "2",
        "Highworth RC A": "2",
        "Radley Athletic Club A": "2",
        "Eynsham Road Runners A": "2",
        "Woodstock Harriers AC A": "2",
        "Hook Norton Harriers A": "2",
        "Oxford Tri A": "2",
        "Bicester AC A": "2",
        "Newbury AC B": "2",
        "Alchester Running Club A": "2",
    }

    # Gender mappings
    gender_mappings = {
        "Men": "Male",
        "U11B": "Male",
        "U11G": "Female",
        "Women": "Female",
        "U9": "Male",  # Will be determined by category
        "U13": "Male",  # Will be determined by category
        "U15": "Male",  # Will be determined by category
        "U17": "Male",  # Will be determined by category
    }

    # Category mappings
    category_mappings = {
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
        ("Male", "U13B"): "U13B",
        ("Female", "U13G"): "U13G",
        ("Female", "U13 Girls"): "U13G",
        ("Male", "U15 Boys"): "U15B",
        ("Female", "U15 Girls"): "U15G",
        ("Male", "U17 Boys"): "U17M",
        ("Female", "U17 Girls"): "U17W",
    }

    # Build category configuration
    category_config = build_default_categories()

    return CompetitionConfig(
        category_config=category_config,
        guest_numbers=guests,
        round_numbers=round_numbers,
        data_base_path=data_base_path,
        mens_divisions=mens_divisions,
        womens_divisions=womens_divisions,
        gender_mappings=gender_mappings,
        category_mappings=category_mappings,
    )
