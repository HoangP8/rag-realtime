"""
LLM completions endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.completions import CompletionRequest, CompletionResponse
from app.models.common import ErrorResponse
from app.services.llm import LLMService
from app.dependencies import get_llm_service

router = APIRouter()


@router.post(
    "/chat",
    response_model=CompletionResponse,
    responses={400: {"model": ErrorResponse}}
)
async def generate_chat_completion(
    request: CompletionRequest,
    llm_service: LLMService = Depends(get_llm_service)
):
    """Generate a chat completion"""
    try:
        response = await llm_service.generate_chat_completion(
            messages=request.messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return CompletionResponse(
            id=response.id,
            created=response.created,
            model=response.model,
            content=response.choices[0].message.content,
            finish_reason=response.choices[0].finish_reason,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
