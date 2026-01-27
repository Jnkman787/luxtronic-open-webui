"""
SavedItem model for My Stuff dashboard.
Stores charts (and future items) saved by users from chat conversations.
"""

import time
import uuid
from typing import Optional, List

from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, Integer, String, Text, JSON
from sqlalchemy.exc import IntegrityError

from open_webui.internal.db import Base, get_db, get_table_name


####################
# SavedItem DB Schema
####################


class SavedItem(Base):
    __tablename__ = get_table_name("saved_item")

    id = Column(String(36), primary_key=True)
    user_id = Column(String(255), nullable=False)
    chat_id = Column(String(255), nullable=True)
    message_id = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # line, bar, pie, scatter
    title = Column(String(500), nullable=False)
    display_order = Column(Integer, nullable=True)
    sql_template = Column(Text, nullable=False)
    series_config = Column(JSON, nullable=True)
    timeframe_type = Column(String(20), nullable=False)  # days, hours
    timeframe_value = Column(Integer, nullable=False)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


####################
# Pydantic Models
####################


class SavedItemModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    chat_id: Optional[str] = None
    message_id: str
    type: str
    title: str
    display_order: Optional[int] = None
    sql_template: str
    series_config: Optional[List[dict]] = None
    timeframe_type: str
    timeframe_value: int
    created_at: int
    updated_at: int


class SavedItemCreateForm(BaseModel):
    chat_id: Optional[str] = None
    message_id: str
    type: str  # line, bar, pie, scatter
    title: str
    sql_template: str
    series_config: Optional[List[dict]] = None
    timeframe_type: str  # days, hours
    timeframe_value: int


class SavedItemUpdateForm(BaseModel):
    title: Optional[str] = None
    display_order: Optional[int] = None


class ReorderItemsForm(BaseModel):
    item_ids: List[str]


####################
# CRUD Operations
####################


class SavedItemsTable:
    def get_items_by_user(self, user_id: str) -> List[SavedItemModel]:
        """Get all saved items for a user, ordered by display_order then created_at."""
        with get_db() as db:
            items = (
                db.query(SavedItem)
                .filter(SavedItem.user_id == user_id)
                .order_by(
                    SavedItem.display_order.asc().nullslast(),
                    SavedItem.created_at.asc()
                )
                .all()
            )
            return [SavedItemModel.model_validate(item) for item in items]

    def get_item_by_id(self, id: str, user_id: str) -> Optional[SavedItemModel]:
        """Get a specific saved item by ID (scoped to user)."""
        with get_db() as db:
            item = (
                db.query(SavedItem)
                .filter(SavedItem.id == id, SavedItem.user_id == user_id)
                .first()
            )
            return SavedItemModel.model_validate(item) if item else None

    def is_message_saved(self, user_id: str, message_id: str) -> bool:
        """Check if a message has already been saved by a user."""
        with get_db() as db:
            item = (
                db.query(SavedItem)
                .filter(
                    SavedItem.user_id == user_id,
                    SavedItem.message_id == message_id
                )
                .first()
            )
            return item is not None

    def create_item(self, user_id: str, form_data: SavedItemCreateForm) -> SavedItemModel:
        """Create a new saved item. Raises IntegrityError if duplicate."""
        with get_db() as db:
            now = int(time.time_ns())
            item = SavedItem(
                id=str(uuid.uuid4()),
                user_id=user_id,
                chat_id=form_data.chat_id,
                message_id=form_data.message_id,
                type=form_data.type,
                title=form_data.title,
                display_order=None,  # New items go at the end
                sql_template=form_data.sql_template,
                series_config=form_data.series_config,
                timeframe_type=form_data.timeframe_type,
                timeframe_value=form_data.timeframe_value,
                created_at=now,
                updated_at=now,
            )
            db.add(item)
            db.commit()
            db.refresh(item)
            return SavedItemModel.model_validate(item)

    def update_item(
        self, id: str, user_id: str, form_data: SavedItemUpdateForm
    ) -> Optional[SavedItemModel]:
        """Update a saved item's title or display_order."""
        with get_db() as db:
            item = (
                db.query(SavedItem)
                .filter(SavedItem.id == id, SavedItem.user_id == user_id)
                .first()
            )
            if not item:
                return None

            if form_data.title is not None:
                item.title = form_data.title
            if form_data.display_order is not None:
                item.display_order = form_data.display_order

            item.updated_at = int(time.time_ns())
            db.commit()
            db.refresh(item)
            return SavedItemModel.model_validate(item)

    def delete_item(self, id: str, user_id: str) -> bool:
        """Delete a saved item. Returns True if deleted, False if not found."""
        with get_db() as db:
            result = (
                db.query(SavedItem)
                .filter(SavedItem.id == id, SavedItem.user_id == user_id)
                .delete()
            )
            db.commit()
            return result > 0

    def reorder_items(self, user_id: str, item_ids: List[str]) -> bool:
        """
        Reorder items by setting display_order based on position in item_ids list.
        Items not in the list will have their display_order set to None.
        """
        with get_db() as db:
            # Reset all display_orders for this user
            db.query(SavedItem).filter(SavedItem.user_id == user_id).update(
                {SavedItem.display_order: None}
            )

            # Set display_order based on position in list
            for idx, item_id in enumerate(item_ids):
                db.query(SavedItem).filter(
                    SavedItem.id == item_id,
                    SavedItem.user_id == user_id
                ).update({SavedItem.display_order: idx})

            db.commit()
            return True


SavedItems = SavedItemsTable()
