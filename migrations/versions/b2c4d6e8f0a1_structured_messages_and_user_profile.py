"""structured_messages_and_user_profile

Remplace :
  - conversations.messages (JSON)  →  table messages (id, conversation_id, role, content, created_at)
  - users.profile (JSON)           →  colonnes users.niveau + users.serie + table user_interets

Revision ID: b2c4d6e8f0a1
Revises: 3e1719684a0e
Create Date: 2026-05-06 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2c4d6e8f0a1"
down_revision: Union[str, Sequence[str], None] = "3e1719684a0e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Table messages ────────────────────────────────────────────────────
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])

    # ── 2. Supprimer conversations.messages (JSON) ───────────────────────────
    op.drop_column("conversations", "messages")

    # ── 3. Colonnes niveau et serie sur users ────────────────────────────────
    op.add_column("users", sa.Column("niveau", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("serie", sa.String(length=50), nullable=True))

    # ── 4. Table user_interets ───────────────────────────────────────────────
    op.create_table(
        "user_interets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("interet", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_interets_user_id", "user_interets", ["user_id"])

    # ── 5. Supprimer users.profile (JSON) ────────────────────────────────────
    op.drop_column("users", "profile")


def downgrade() -> None:
    # Remet profile JSON (vide — les données ne sont pas migrées en sens inverse)
    op.add_column("users", sa.Column("profile", sa.JSON(), nullable=True))

    op.drop_index("ix_user_interets_user_id", table_name="user_interets")
    op.drop_table("user_interets")

    op.drop_column("users", "serie")
    op.drop_column("users", "niveau")

    # Remet messages JSON avec valeur par défaut tableau vide
    op.add_column(
        "conversations",
        sa.Column(
            "messages",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
    )

    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")
