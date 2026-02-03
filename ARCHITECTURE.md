# PyResults - Refactored Architecture

## Overview

This document describes the refactored architecture of PyResults, which now follows SOLID principles and modern object-oriented design patterns.

## Architecture Overview

The application is organized into distinct layers following clean architecture principles:

```
pyresults/
├── domain/          # Domain models (entities)
├── repositories/    # Data access layer (repositories)
├── config/          # Configuration management
├── services/        # Business logic layer
├── output/          # Output generation layer
└── results_processor.py  # Application orchestrator
```

## SOLID Principles Applied

### 1. Single Responsibility Principle (SRP)

Each class has one clearly defined responsibility:

- **Domain Entities**: Each entity (Athlete, Team, Score, Category) encapsulates only its own data and behavior
- **Services**: Each service handles one specific aspect of business logic
  - `RaceProcessorService`: Processes raw race files
  - `IndividualScoreService`: Aggregates individual scores
  - `TeamScoreService`: Aggregates team scores
  - `TeamScoringService`: Calculates team scores from race results
- **Repositories**: Each repository handles one type of data access
  - `CsvRaceResultRepository`: Race result persistence
  - `CsvScoreRepository`: Score persistence

### 2. Open/Closed Principle (OCP)

The system is open for extension but closed for modification:

- **Output Generators**: New output formats can be added by implementing `IOutputGenerator` without modifying existing code
- **Repositories**: New storage backends can be added by implementing repository interfaces
- **Category Configuration**: New categories can be added through configuration without code changes

### 3. Liskov Substitution Principle (LSP)

All implementations can be substituted for their abstractions:

- Any `IOutputGenerator` implementation can replace another
- Any repository implementation can be swapped
- Services depend on interfaces, not concrete classes

### 4. Interface Segregation Principle (ISP)

Clients depend only on interfaces they use:

- `IOutputGenerator`: Simple, focused interface with only `generate()` method
- `IRaceResultRepository`: Focused on race result operations
- `IScoreRepository`: Focused on score operations

### 5. Dependency Inversion Principle (DIP)

High-level modules depend on abstractions, not concrete implementations:

- `ResultsProcessor` depends on repository interfaces, not concrete implementations
- Services are injected with their dependencies
- Configuration is injected, not globally imported
- All coupling is through abstractions

## Layer Details

### Domain Layer (`domain/`)

**Purpose**: Contains core business entities with no external dependencies

**Classes**:
- `Athlete`: Represents an individual athlete with validation
- `Team`: Represents a team with scoring logic
- `Score`: Represents cumulative scores with calculation logic
- `Category`: Represents competition categories with rules
- `RaceResult`: Represents results of a single race
- `Round`: Represents a competition round

**Key Improvements**:
- Replaced primitive obsession (strings, dicts) with rich domain objects
- Encapsulated business rules within entities
- Added validation at entity creation
- Type safety through dataclasses

### Repository Layer (`repositories/`)

**Purpose**: Abstracts data access from business logic

**Interfaces**:
- `IRaceResultRepository`: Contract for race result storage
- `IScoreRepository`: Contract for score storage

**Implementations**:
- `CsvRaceResultRepository`: CSV-based race result storage
- `CsvScoreRepository`: CSV-based score storage

**Key Improvements**:
- Business logic no longer knows about file system
- Easy to test with mock repositories
- Can swap to database without changing business logic
- Centralized data access logic

### Configuration Layer (`config/`)

**Purpose**: Manages application configuration in an injectable way

**Classes**:
- `CompetitionConfig`: Main configuration class
- `CategoryConfig`: Category definitions and mappings
- `build_default_config()`: Factory for default configuration

**Key Improvements**:
- Configuration is injected, not globally imported
- Can have multiple configurations (testing, different competitions)
- Extensible without code modification
- Type-safe configuration objects

### Service Layer (`services/`)

**Purpose**: Contains business logic and orchestrates operations

**Services**:
- `RaceProcessorService`: Processes raw race files into domain objects
- `IndividualScoreService`: Aggregates individual athlete scores across rounds
- `TeamScoreService`: Aggregates team scores across rounds
- `TeamScoringService`: Calculates team scores from race results

**Key Improvements**:
- Decomposed God classes into focused services
- Single responsibility for each service
- Testable through dependency injection
- Clear separation of concerns

### Output Layer (`output/`)

**Purpose**: Generates output in different formats

**Interface**:
- `IOutputGenerator`: Contract for output generation

**Implementations**:
- `ExcelOutputGenerator`: Generates Excel files
- `PdfOutputGenerator`: Generates PDF files

**Key Improvements**:
- Easy to add new output formats
- Output generation separated from business logic
- Consistent interface for all generators

### Application Orchestrator

**Class**: `ResultsProcessor`

**Purpose**: Wires together all components and orchestrates the workflow

**Key Improvements**:
- All dependencies injected through constructor
- Clear workflow orchestration
- Testable by mocking dependencies
- Single entry point for the application

## Design Patterns Used

### 1. Repository Pattern
Abstracts data access behind interfaces, allowing different storage implementations.

### 2. Strategy Pattern
Output generators can be swapped or extended without modifying client code.

### 3. Dependency Injection
All dependencies are injected, making the system testable and flexible.

### 4. Factory Pattern
Configuration builders (`build_default_config()`, `build_default_categories()`) create complex objects.

## Benefits of This Architecture

### Testability
- All dependencies can be mocked
- Services can be tested in isolation
- No file system dependencies in tests
- Clear interfaces for test doubles

### Maintainability
- Each class has one reason to change
- Clear separation of concerns
- Easy to locate and fix bugs
- Self-documenting code structure

### Extensibility
- New categories via configuration
- New output formats via `IOutputGenerator`
- New storage backends via repository interfaces
- New scoring rules via strategy pattern

### Flexibility
- Can swap implementations at runtime
- Multiple configurations possible
- Easy to add new features
- Supports different competition formats

## Migration from Old Code

The old code structure has been preserved but is no longer used by the new entry point:

- Old: `results.py` (God class)
- New: `results_processor.py` (orchestrator)

- Old: `race_result.py` (mixed responsibilities)
- New: `services/race_processor_service.py` (focused service)

- Old: `CONFIG.py` (global constants)
- New: `config/competition_config.py` (injectable configuration)

- Old: `create_excel()` function
- New: `output/ExcelOutputGenerator` class

- Old: `create_pdf()` function
- New: `output/PdfOutputGenerator` class

## Usage

### Basic Usage

```python
from pyresults.results_processor import ResultsProcessor
from pyresults.config import build_default_config

# Build configuration
config = build_default_config()

# Create processor with dependency injection
processor = ResultsProcessor(config)

# Process rounds
processor.process_rounds(
    rounds_to_process=["r1", "r2"],
    create_excel=True,
    create_pdf=True
)
```

### Testing with Mocks

```python
# Create mock repositories
mock_race_repo = Mock(spec=IRaceResultRepository)
mock_score_repo = Mock(spec=IScoreRepository)

# Inject mocks into service
service = IndividualScoreService(
    config=test_config,
    race_result_repo=mock_race_repo,
    score_repo=mock_score_repo
)

# Test in isolation
service.update_scores_for_category("U13B")

# Verify behavior
mock_race_repo.load_race_result.assert_called()
```

### Custom Configuration

```python
from pathlib import Path
from pyresults.config import CompetitionConfig, build_default_categories

# Create custom configuration
custom_config = CompetitionConfig(
    category_config=build_default_categories(),
    guest_numbers={"1234", "5678"},
    round_numbers=["r1", "r2", "r3"],
    data_base_path=Path("./custom_data"),
    mens_divisions={},
    womens_divisions={},
    gender_mappings={},
    category_mappings={}
)

processor = ResultsProcessor(custom_config)
```

## Future Improvements

### Potential Enhancements

1. **Strategy Pattern for Scoring**: Create scoring strategy interfaces for different competition types
2. **Event Sourcing**: Track all changes to scores for audit trail
3. **Command Pattern**: Make operations undoable
4. **Observer Pattern**: Notify when scores change
5. **Database Backend**: Implement database repositories
6. **API Layer**: Add REST API for remote access
7. **Async Processing**: Use async/await for better performance
8. **Validation Layer**: Add comprehensive input validation
9. **Logging**: Add structured logging throughout
10. **Configuration Files**: Load configuration from YAML/JSON

### Testing Strategy

1. **Unit Tests**: Test each class in isolation with mocks
2. **Integration Tests**: Test service layer with real repositories
3. **End-to-End Tests**: Test complete workflow
4. **Property-Based Tests**: Test domain invariants
5. **Performance Tests**: Ensure scalability

## Conclusion

This refactoring transforms pyresults from a procedural script with God classes into a well-structured, SOLID-compliant application. The new architecture is:

- **Testable**: All dependencies can be mocked
- **Maintainable**: Clear structure and responsibilities
- **Extensible**: Easy to add new features
- **Flexible**: Can adapt to different requirements
- **Professional**: Follows industry best practices

The investment in proper architecture pays dividends in reduced bugs, faster feature development, and easier maintenance.
