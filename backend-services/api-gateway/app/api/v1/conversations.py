"""
Conversation endpoints
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.conversations import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse
)
from app.services.conversations import ConversationService
from app.core.dependencies import get_conversation_service, get_current_user

router = APIRouter()


@router.get("/", response_model=List[ConversationResponse])
async def get_conversations(
    conversation_service: ConversationService = Depends(get_conversation_service),
    user_id: UUID = Depends(get_current_user)
):
    """Get all conversations for the current user"""
    try:
        conversations = await conversation_service.get_user_conversations(user_id)
        return conversations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    conversation_service: ConversationService = Depends(get_conversation_service),
    user_id: UUID = Depends(get_current_user)
):
    """Create a new conversation"""
    try:
        conversation = await conversation_service.create_conversation(user_id, conversation_data)
        return conversation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    conversation_service: ConversationService = Depends(get_conversation_service),
    user_id: UUID = Depends(get_current_user)
):
    """Get a specific conversation"""
    try:
        conversation = await conversation_service.get_conversation(user_id, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    conversation_data: ConversationUpdate,
    conversation_service: ConversationService = Depends(get_conversation_service),
    user_id: UUID = Depends(get_current_user)
):
    """Update a conversation"""
    try:
        conversation = await conversation_service.update_conversation(
            user_id, conversation_id, conversation_data
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    conversation_service: ConversationService = Depends(get_conversation_service),
    user_id: UUID = Depends(get_current_user)
):
    """Delete a conversation"""
    try:
        success = await conversation_service.delete_conversation(user_id, conversation_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: UUID,
    conversation_service: ConversationService = Depends(get_conversation_service),
    user_id: UUID = Depends(get_current_user)
):
    """Get all messages for a conversation"""
    try:
        messages = await conversation_service.get_conversation_messages(user_id, conversation_id)
        return messages
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def create_message(
    conversation_id: UUID,
    message_data: MessageCreate,
    conversation_service: ConversationService = Depends(get_conversation_service),
    user_id: UUID = Depends(get_current_user)
):
    """Create a new message in a conversation"""
    try:
        message = await conversation_service.create_message(user_id, conversation_id, message_data)
        return message
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
