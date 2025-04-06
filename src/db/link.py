from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Link(Base):

    chat_id: Mapped[int] = mapped_column(Integer, nullable=False)
    link: Mapped[str] = mapped_column(String)
    tags: Mapped[list[str]] = mapped_column(JSON)
    filters: Mapped[list[str]] = mapped_column(JSON)

    def __repr__(self):
        return f"<Link(id={self.id}, chat_id={self.chat_id}, link={self.link})>"
