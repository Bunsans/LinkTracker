from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.chat import Chat
    from src.db.link import Link


class ChatLinkAssociation(Base):

    link_id: Mapped[int] = mapped_column(ForeignKey("links.id"))
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"))

    tags: Mapped[list[str]] = mapped_column(JSON)
    filters: Mapped[list[str]] = mapped_column(JSON)

    chat: Mapped["Chat"] = relationship(back_populates="links_details", viewonly=True)
    link: Mapped["Link"] = relationship(back_populates="chats_details", viewonly=True)

    __table_args__ = (UniqueConstraint("link_id", "chat_id", name="_link_chat_uc"),)
