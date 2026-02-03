"""Example usage of the refactored pyresults architecture.

This script demonstrates how to use the new SOLID-based architecture
with dependency injection and proper abstractions.
"""

from pyresults.config import build_default_config
from pyresults.results_processor import ResultsProcessor


def main():
    """Main example demonstrating the new architecture."""

    print("=" * 60)
    print("PyResults - Refactored Architecture Example")
    print("=" * 60)
    print()

    # 1. Build configuration (can be customized or loaded from file)
    print("Step 1: Building configuration...")
    config = build_default_config()
    print(f"  - Configured {len(config.category_config.get_all_categories())} categories")
    print(f"  - Processing rounds: {', '.join(config.round_numbers)}")
    print()

    # 2. Create processor with dependency injection
    print("Step 2: Initializing ResultsProcessor with dependency injection...")
    processor = ResultsProcessor(config)
    print("  - Race result repository initialized")
    print("  - Score repository initialized")
    print("  - Services initialized")
    print()

    # 3. Process rounds
    print("Step 3: Processing race results...")
    rounds_to_process = ["r1", "r2"]  # Example: process first two rounds

    try:
        processor.process_rounds(
            rounds_to_process=rounds_to_process, create_excel=True, create_pdf=True
        )
        print("  ✓ Race results processed successfully")
        print("  ✓ Individual scores aggregated")
        print("  ✓ Team scores aggregated")
        print("  ✓ Output files generated")
    except FileNotFoundError as e:
        print(f"  ⚠ Warning: {e}")
        print("  (This is expected if input data files don't exist)")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return

    print()
    print("=" * 60)
    print("Example completed successfully!")
    print()
    print("Key Benefits of New Architecture:")
    print("  • Testable: All dependencies can be mocked")
    print("  • Maintainable: Clear separation of concerns")
    print("  • Extensible: Easy to add new features")
    print("  • Flexible: Can swap implementations")
    print("=" * 60)


def demonstrate_testing():
    """Demonstrate how the new architecture enables easy testing."""
    from unittest.mock import Mock

    from pyresults.repositories import IRaceResultRepository, IScoreRepository
    from pyresults.services import IndividualScoreService

    print()
    print("=" * 60)
    print("Testing Example - Using Mocks")
    print("=" * 60)
    print()

    # Create mock dependencies
    mock_race_repo = Mock(spec=IRaceResultRepository)
    mock_score_repo = Mock(spec=IScoreRepository)
    mock_config = build_default_config()

    # Mock the exists method to return False (no races)
    mock_race_repo.exists.return_value = False
    mock_score_repo.exists.return_value = False
    mock_score_repo.load_scores.return_value = []

    # Create service with mocked dependencies
    service = IndividualScoreService(
        config=mock_config, race_result_repo=mock_race_repo, score_repo=mock_score_repo
    )

    print("Created IndividualScoreService with mock dependencies")
    print()

    # Test the service
    try:
        service.update_scores_for_category("U13B")
        print("✓ Service executed without errors")
        print("✓ No actual file system access occurred")
        print("✓ Service is fully testable in isolation")
    except Exception as e:
        print(f"✗ Error: {e}")

    print()
    print("=" * 60)


def demonstrate_extensibility():
    """Demonstrate how easy it is to extend the system."""
    from pyresults.output import IOutputGenerator

    print()
    print("=" * 60)
    print("Extensibility Example - Custom Output Generator")
    print("=" * 60)
    print()

    # Example: Custom JSON output generator
    class JsonOutputGenerator(IOutputGenerator):
        """Example custom output generator for JSON format."""

        def __init__(self, config, output_path):
            self.config = config
            self.output_path = output_path

        def generate(self):
            """Generate JSON output."""
            print(f"  → Generating JSON output to {self.output_path}")
            print("  → (Implementation would go here)")

    print("Created custom JsonOutputGenerator")
    print("  • Implements IOutputGenerator interface")
    print("  • Can be used alongside Excel and PDF generators")
    print("  • No changes to existing code required")
    print()
    print("=" * 60)


if __name__ == "__main__":
    # Run main example
    main()

    # Demonstrate testing capabilities
    demonstrate_testing()

    # Demonstrate extensibility
    demonstrate_extensibility()
