from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .chat_link_association import ChatLinkAssociation
    from .link import Link


class Chat(Base):
    tg_chat_id: Mapped[int] = mapped_column(unique=True)
    links: Mapped[list["Link"]] = relationship(
        secondary="chat_link_associations",
        back_populates="chats",
    )
    links_details: Mapped[list["ChatLinkAssociation"]] = relationship(
        back_populates="chat",
        viewonly=True,
    )
