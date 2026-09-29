from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class SyncStatus(Base):
    __tablename__ = "sync_status"

    source: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    last_success_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="UNKNOWN",
    )