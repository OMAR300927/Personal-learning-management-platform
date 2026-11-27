from sqlalchemy.orm import DeclarativeBase


class DeletionLedgerBase(DeclarativeBase):
    """Base metadata for tables stored outside the application database."""
