"""Output generator interfaces."""

from abc import ABC, abstractmethod


class IOutputGenerator(ABC):
    """Abstract interface for output generation.

    This interface defines the contract for generating output files,
    allowing different implementations (Excel, PDF) without changing
    client code.
    """

    @abstractmethod
    def generate(self) -> None:
        """Generate output file(s).

        This method should create the output file(s) based on the
        current state of scores and results.
        """
        pass
