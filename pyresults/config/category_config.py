"""Category configuration module.

Defines category configurations using domain objects rather than
scattered dictionaries.
"""

from pyresults.domain import Category, CategoryType
from pyresults.domain.category import Gender


class CategoryConfig:
    """Configuration for competition categories.

    Encapsulates category definitions and mappings, replacing hard-coded
    dictionaries in CONFIG.py.
    """

    def __init__(self, categories: dict[str, Category]):
        """Initialize with category definitions.

        Args:
            categories: Dictionary mapping category codes to Category objects
        """
        self.categories = categories

    def get_category(self, code: str) -> Category:
        """Get category by code.

        Args:
            code: Category code (e.g., "U13B", "MV40")

        Returns:
            Category object

        Raises:
            ValueError: If category code not found
        """
        if code not in self.categories:
            raise ValueError(f"Unknown category code: {code}")
        return self.categories[code]

    def get_all_categories(self) -> list[Category]:
        """Get all configured categories."""
        return list(self.categories.values())

    def get_categories_by_type(self, category_type: CategoryType) -> list[Category]:
        """Get all categories of a specific type.

        Args:
            category_type: Type to filter by

        Returns:
            List of matching categories
        """
        return [c for c in self.categories.values() if c.category_type == category_type]

    def get_race_name_for_category(self, category_code: str) -> str:
        """Get the race name for a category.

        Args:
            category_code: Category code

        Returns:
            Race name this category belongs to
        """
        return self.get_category(category_code).race_name

    def get_team_size_for_category(self, category_code: str) -> int:
        """Get team size for a team category.

        Args:
            category_code: Category code

        Returns:
            Number of athletes per team

        Raises:
            ValueError: If category is not a team category
        """
        category = self.get_category(category_code)
        if not category.is_team_category():
            raise ValueError(f"Category {category_code} is not a team category")
        if category.team_size is None:
            raise ValueError(f"Team category {category_code} has no team_size defined")
        return category.team_size


def build_default_categories() -> CategoryConfig:
    """Build the default Oxfordshire XC League category configuration.

    This function constructs the category configuration matching the
    original hard-coded CATEGORIES and RACE_MAPPINGS from CONFIG.py.

    Returns:
        CategoryConfig with all standard categories defined
    """
    categories = {}

    # Youth categories
    youth_categories = [
        ("U9B", "Under 9 Boys", Gender.MALE, "U9", 3),
        ("U9G", "Under 9 Girls", Gender.FEMALE, "U9", 3),
        ("U11B", "Under 11 Boys", Gender.MALE, "U11", 3),
        ("U11G", "Under 11 Girls", Gender.FEMALE, "U11", 3),
        ("U13B", "Under 13 Boys", Gender.MALE, "U13", 3),
        ("U13G", "Under 13 Girls", Gender.FEMALE, "U13", 3),
        ("U15B", "Under 15 Boys", Gender.MALE, "U15", 3),
        ("U15G", "Under 15 Girls", Gender.FEMALE, "U15", 3),
        ("U17M", "Under 17 Men", Gender.MALE, "U17", 3),
        ("U17W", "Under 17 Women", Gender.FEMALE, "U17", 3),
    ]

    for code, name, gender, race_name, team_size in youth_categories:
        categories[code] = Category(
            code=code,
            name=name,
            category_type=CategoryType.TEAM,
            gender=gender,
            race_name=race_name,
            team_size=team_size,
            age_group=code[:3],  # e.g., "U13"
        )

    # Senior and veteran categories
    adult_individual_categories = [
        # Men's categories
        ("U20M", "Under 20 Men", Gender.MALE, "Men", "U20"),
        ("SM", "Senior Men", Gender.MALE, "Men", "Senior"),
        ("MV40", "Men V40", Gender.MALE, "Men", "V40"),
        ("MV50", "Men V50", Gender.MALE, "Men", "V50"),
        ("MV60", "Men V60", Gender.MALE, "Men", "V60"),
        ("MV70", "Men V70", Gender.MALE, "Men", "V70"),
        # Women's categories
        ("U20W", "Under 20 Women", Gender.FEMALE, "Women", "U20"),
        ("SW", "Senior Women", Gender.FEMALE, "Women", "Senior"),
        ("WV40", "Women V40", Gender.FEMALE, "Women", "V40"),
        ("WV50", "Women V50", Gender.FEMALE, "Women", "V50"),
        ("WV60", "Women V60", Gender.FEMALE, "Women", "V60"),
        ("WV70", "Women V70", Gender.FEMALE, "Women", "V70"),
    ]

    for code, name, gender, race_name, age_group in adult_individual_categories:
        categories[code] = Category(
            code=code,
            name=name,
            category_type=CategoryType.INDIVIDUAL,
            gender=gender,
            race_name=race_name,
            age_group=age_group,
        )

    # Team categories for adult races (all ages contribute to team scores)
    categories["Men"] = Category(
        code="Men",
        name="Men's Teams",
        category_type=CategoryType.TEAM,
        gender=Gender.MALE,
        race_name="Men",
        team_size=7,
    )

    categories["Women"] = Category(
        code="Women",
        name="Women's Teams",
        category_type=CategoryType.TEAM,
        gender=Gender.FEMALE,
        race_name="Women",
        team_size=4,
    )

    # Overall categories (for league standings across all age groups)
    categories["MensOverall"] = Category(
        code="MensOverall",
        name="Men's Overall",
        category_type=CategoryType.OVERALL,
        gender=Gender.MALE,
        race_name="Men",
    )

    categories["WomensOverall"] = Category(
        code="WomensOverall",
        name="Women's Overall",
        category_type=CategoryType.OVERALL,
        gender=Gender.FEMALE,
        race_name="Women",
    )

    return CategoryConfig(categories)
