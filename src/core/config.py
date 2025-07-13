"""Configuration management using Pydantic settings."""

from typing import Optional, Tuple
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    
    # Database
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/minesweeper_benchmark",
        description="PostgreSQL database URL"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis URL for caching and queuing"
    )
    
    # Application
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Debug mode")
    secret_key: str = Field(default="change-me-in-production", description="Secret key for sessions")
    
    # Model Settings
    default_model_temperature: float = Field(default=0.7, description="Default temperature for model generation")
    default_max_tokens: int = Field(default=1000, description="Default max tokens for model generation")
    model_timeout: int = Field(default=30, description="Timeout for model API calls in seconds")
    
    # Game Settings
    default_board_rows: int = Field(default=16, description="Default number of rows")
    default_board_cols: int = Field(default=30, description="Default number of columns")
    default_mine_count: int = Field(default=99, description="Default number of mines")
    max_moves_per_game: int = Field(default=500, description="Maximum moves allowed per game")
    
    # Evaluation Settings
    evaluation_batch_size: int = Field(default=10, description="Number of games to evaluate in parallel")
    evaluation_timeout: int = Field(default=300, description="Timeout for evaluation in seconds")
    
    @property
    def default_board_size(self) -> Tuple[int, int]:
        """Get default board size as tuple."""
        return (self.default_board_rows, self.default_board_cols)


# Global settings instance
settings = Settings()