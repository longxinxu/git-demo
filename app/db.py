from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, ContentItem, ContentStatus, ContentVersion

DB_PATH = Path(__file__).resolve().parent.parent / "data.db"


def get_engine():
    return create_engine(f"sqlite:///{DB_PATH}", future=True)


@contextmanager
def get_session() -> Session:
    SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False, future=True)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _table_exists(session: Session, table_name: str) -> bool:
    return inspect(session.bind).has_table(table_name)


def _migrate_legacy_contents(session: Session) -> None:
    if not _table_exists(session, "contents"):
        return

    legacy_rows = session.execute(
        text(
            """
            SELECT id, title, category, summary, body, quality_score, status, source, created_at
            FROM contents
            """
        )
    ).mappings().all()

    if not legacy_rows:
        session.execute(text("DROP TABLE IF EXISTS contents"))
        return

    for row in legacy_rows:
        legacy_status = row["status"]
        mapped_status = ContentStatus.pending_review.value
        if legacy_status in {"approved", "rejected", "archived"}:
            mapped_status = legacy_status
        elif legacy_status == "flagged":
            mapped_status = ContentStatus.rejected.value

        created_at = datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.utcnow()
        item = ContentItem(
            id=row["id"],
            title=row["title"],
            category=row["category"],
            summary=row["summary"],
            source=row["source"],
            status=mapped_status,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(item)
        session.flush()

        version = ContentVersion(
            content_item_id=item.id,
            version_no=1,
            body=row["body"],
            change_note="migrated from contents",
            created_at=created_at,
        )
        session.add(version)

    session.execute(text("DROP TABLE IF EXISTS contents"))


def init_db() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        _migrate_legacy_contents(session)
        session.commit()
