from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .chat import Chat
    from .chat_link_association import ChatLinkAssociation


class Link(Base):
    link: Mapped[str] = mapped_column(String)
    count_chats: Mapped[int] = mapped_column(Integer, default=1)
    last_update: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    chats: Mapped[list["Chat"]] = relationship(
        secondary="chat_link_associations",
        back_populates="links",
    )
    chats_details: Mapped[list["ChatLinkAssociation"]] = relationship(
        back_populates="link",
        viewonly=True,
    )
