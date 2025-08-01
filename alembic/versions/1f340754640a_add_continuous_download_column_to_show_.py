"""add 'continuous_download' column to show table

Revision ID: 1f340754640a
Revises: 7508237d5bc2
Create Date: 2025-06-22 13:46:01.973406

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1f340754640a"
down_revision: Union[str, None] = "7508237d5bc2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "show",
        sa.Column(
            "continuous_download",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("show", "continuous_download")
    # ### end Alembic commands ###
