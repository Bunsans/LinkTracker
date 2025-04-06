"""Add filters and tags

Revision ID: 49fba33c67e4
Revises: d0c6fffe82f5
Create Date: 2025-04-05 20:05:08.062728

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "49fba33c67e4"
down_revision: Union[str, None] = "d0c6fffe82f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("links", sa.Column("tags", sa.JSON(), nullable=False))
    op.add_column("links", sa.Column("filters", sa.JSON(), nullable=False))
    op.drop_constraint("links_chat_id_key", "links", type_="unique")
    op.drop_constraint("links_link_key", "links", type_="unique")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_unique_constraint("links_link_key", "links", ["link"])
    op.create_unique_constraint("links_chat_id_key", "links", ["chat_id"])
    op.drop_column("links", "filters")
    op.drop_column("links", "tags")
