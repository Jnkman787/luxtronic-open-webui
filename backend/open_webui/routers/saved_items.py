"""
API Router for Saved Items (My Stuff dashboard).
Handles CRUD operations for user-saved charts.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from open_webui.models.saved_items import (
    SavedItems,
    SavedItemModel,
    SavedItemCreateForm,
    SavedItemUpdateForm,
    ReorderItemsForm,
)
from open_webui.utils.auth import get_verified_user
from open_webui.env import SRC_LOG_LEVELS

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS.get("MODELS", logging.INFO))

router = APIRouter()


############################
# Response Models
############################


class MessageSavedResponse(BaseModel):
    saved: bool


class SuccessResponse(BaseModel):
    success: bool


############################
# Get Saved Items
############################


@router.get("/", response_model=List[SavedItemModel])
async def get_saved_items(user=Depends(get_verified_user)):
    """
    Get all saved items for the current user.
    Items are ordered by display_order (if set), then by created_at ascending.
    """
    return SavedItems.get_items_by_user(user.id)


############################
# Check if Message is Saved
############################


@router.get("/check/{message_id}", response_model=MessageSavedResponse)
async def check_message_saved(message_id: str, user=Depends(get_verified_user)):
    """
    Check if a message has already been saved by the current user.
    Used to show/hide the "Add to My Stuff" button in chat.
    """
    saved = SavedItems.is_message_saved(user.id, message_id)
    return MessageSavedResponse(saved=saved)


############################
# Get Saved Item by ID
############################


@router.get("/{item_id}", response_model=Optional[SavedItemModel])
async def get_saved_item_by_id(item_id: str, user=Depends(get_verified_user)):
    """
    Get a specific saved item by ID.
    """
    item = SavedItems.get_item_by_id(item_id, user.id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved item not found"
        )
    return item


############################
# Create Saved Item
############################


@router.post("/", response_model=SavedItemModel)
async def create_saved_item(
    form_data: SavedItemCreateForm,
    user=Depends(get_verified_user)
):
    """
    Save a new item to My Stuff.
    Returns 400 if the message has already been saved.
    """
    try:
        return SavedItems.create_item(user.id, form_data)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This item has already been saved"
        )
    except Exception as e:
        log.exception(f"Failed to create saved item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save item"
        )


############################
# Update Saved Item
############################


@router.patch("/{item_id}", response_model=SavedItemModel)
async def update_saved_item(
    item_id: str,
    form_data: SavedItemUpdateForm,
    user=Depends(get_verified_user)
):
    """
    Update a saved item's title, display_order, or series_config.
    """
    item = SavedItems.update_item(item_id, user.id, form_data)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved item not found"
        )
    return item


############################
# Delete Saved Item
############################


@router.delete("/{item_id}", response_model=SuccessResponse)
async def delete_saved_item(item_id: str, user=Depends(get_verified_user)):
    """
    Delete a saved item.
    """
    deleted = SavedItems.delete_item(item_id, user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved item not found"
        )
    return SuccessResponse(success=True)


############################
# Reorder Saved Items
############################


@router.post("/reorder", response_model=SuccessResponse)
async def reorder_saved_items(
    form_data: ReorderItemsForm,
    user=Depends(get_verified_user)
):
    """
    Reorder saved items by providing an ordered list of item IDs.
    Items will be assigned display_order values based on their position in the list.
    """
    SavedItems.reorder_items(user.id, form_data.item_ids)
    return SuccessResponse(success=True)
