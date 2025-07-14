"""Placeholder for reasoning judge - implementation moved to reasoning_judge.py"""

from .reasoning_judge import ReasoningJudge

# For backward compatibility
class BatchJudge(ReasoningJudge):
    """Backward compatibility alias for ReasoningJudge."""
    pass