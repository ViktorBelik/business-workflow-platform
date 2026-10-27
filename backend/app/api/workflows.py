from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.infrastructure.database import get_session
from backend.app.schemas.workflow import (
    WorkflowCreate,
    WorkflowRead,
    WorkflowUpdate,
)
from backend.app.services.workflow import (
    create_workflow,
    get_workflow,
    get_workflows,
    update_workflow,
)

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


@router.get(
    "",
    response_model=list[WorkflowRead],
    status_code=status.HTTP_200_OK,
)
async def get_workflows_endpoint(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[WorkflowRead]:
    workflows = await get_workflows(session=session)

    return [WorkflowRead.model_validate(workflow) for workflow in workflows]


@router.get(
    "/{workflow_id}",
    response_model=WorkflowRead,
    status_code=status.HTTP_200_OK,
)
async def get_workflow_endpoint(
    workflow_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WorkflowRead:
    workflow = await get_workflow(
        session=session,
        workflow_id=workflow_id,
    )

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    return WorkflowRead.model_validate(workflow)


@router.put(
    "/{workflow_id}",
    response_model=WorkflowRead,
    status_code=status.HTTP_200_OK,
)
async def update_workflow_endpoint(
    workflow_id: UUID,
    data: WorkflowUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WorkflowRead:
    workflow = await update_workflow(
        session=session,
        workflow_id=workflow_id,
        data=data,
    )

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    return WorkflowRead.model_validate(workflow)
