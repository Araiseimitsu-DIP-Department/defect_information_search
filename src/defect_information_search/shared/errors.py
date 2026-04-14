from __future__ import annotations


class AppError(Exception):
    """Base class for application-level errors."""


class RepositoryError(AppError):
    """Raised when a repository cannot complete a data access operation."""

