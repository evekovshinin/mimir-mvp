"""DB initialization handler."""
from mimir.output import print_success, print_db_initialized
from mimir.db import db_manager


def handle_init(database_url: str | None = None) -> None:
    """Initialize database."""
    from mimir.config import settings

    url = database_url or settings.database_url
    print_success(f"Initializing database: {url}")
    db_manager.init_db(url)
    print_db_initialized()
