from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Chat(Base):
    chat_id: Mapped[int] = mapped_column(unique=True)
