import logging


def configure_logging(level: str) -> None:
    """Configure application-wide logging with the requested severity level."""
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
