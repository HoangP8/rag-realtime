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
from app.core.dependencies import get_conversation_service, get_current_user_and_token

router = APIRouter()


@router.get("/", response_model=List[ConversationResponse])
async def get_conversations(
    conversation_service: ConversationService = Depends(get_conversation_service),
    user_data = Depends(get_current_user_and_token)
):
    """Get all conversations for the current user"""
    try:
        user_id = user_data["user_id"]
        token = user_data["token"]
        conversations = await conversation_service.get_user_conversations(user_id, token)
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
    user_data = Depends(get_current_user_and_token)
):
    """Create a new conversation"""
    try:
        user_id = user_data["user_id"]
        token = user_data["token"]
        conversation = await conversation_service.create_conversation(user_id, conversation_data, token)
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
    user_data = Depends(get_current_user_and_token)
):
    """Get a specific conversation"""
    try:
        token = user_data["token"]
        conversation = await conversation_service.get_conversation(conversation_id, token)
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
    user_data = Depends(get_current_user_and_token)
):
    """Update a conversation"""
    try:
        token = user_data["token"]
        conversation = await conversation_service.update_conversation(
            conversation_id, conversation_data, token
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
    user_data = Depends(get_current_user_and_token)
):
    """Delete a conversation"""
    try:
        token = user_data["token"]
        success = await conversation_service.delete_conversation(conversation_id, token)
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
    user_data = Depends(get_current_user_and_token)
):
    """Get all messages for a conversation"""
    try:
        token = user_data["token"]
        messages = await conversation_service.get_conversation_messages(conversation_id, token)
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
    user_data = Depends(get_current_user_and_token)
):
    """Create a new message in a conversation"""
    try:
        token = user_data["token"]
        message = await conversation_service.create_message(conversation_id, message_data, token)
        return message
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
