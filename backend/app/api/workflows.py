from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.infrastructure.database import get_session
from backend.app.schemas.workflow import WorkflowCreate, WorkflowRead
from backend.app.services.workflow import create_workflow

router = APIRouter(
    prefix="/workflows",
    tags=["workflows"],
)


@router.post(
    "",
    response_model=WorkflowRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow_endpoint(
    data: WorkflowCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WorkflowRead:
    workflow = await create_workflow(
        session=session,
        data=data,
    )

    return WorkflowRead.model_validate(workflow)
