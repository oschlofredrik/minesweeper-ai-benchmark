"""Custom exceptions for the Minesweeper benchmark platform."""


class MinesweeperBenchmarkError(Exception):
    """Base exception for all custom errors."""
    pass


class GameError(MinesweeperBenchmarkError):
    """Base exception for game-related errors."""
    pass


class InvalidMoveError(GameError):
    """Raised when an invalid move is attempted."""
    pass


class GameAlreadyFinishedError(GameError):
    """Raised when trying to make a move on a finished game."""
    pass


class InvalidBoardConfigError(GameError):
    """Raised when board configuration is invalid."""
    pass


class ModelError(MinesweeperBenchmarkError):
    """Base exception for model-related errors."""
    pass


class ModelTimeoutError(ModelError):
    """Raised when model API call times out."""
    pass


class ModelAPIError(ModelError):
    """Raised when model API returns an error."""
    pass


class InvalidModelResponseError(ModelError):
    """Raised when model response cannot be parsed."""
    pass


class EvaluationError(MinesweeperBenchmarkError):
    """Base exception for evaluation-related errors."""
    pass


class TaskNotFoundError(EvaluationError):
    """Raised when a task cannot be found."""
    pass


class MetricsCalculationError(EvaluationError):
    """Raised when metrics calculation fails."""
    pass


class StorageError(MinesweeperBenchmarkError):
    """Base exception for storage-related errors."""
    pass


class DatabaseConnectionError(StorageError):
    """Raised when database connection fails."""
    pass


class DataIntegrityError(StorageError):
    """Raised when data integrity is compromised."""
    pass