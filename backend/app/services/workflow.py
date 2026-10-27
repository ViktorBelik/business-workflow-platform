from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.infrastructure.models.workflow import Workflow
from backend.app.schemas.workflow import WorkflowCreate, WorkflowUpdate


async def create_workflow(
    session: AsyncSession,
    data: WorkflowCreate,
) -> Workflow:
    workflow = Workflow(
        name=data.name,
        description=data.description,
    )

    session.add(workflow)
    await session.commit()
    await session.refresh(workflow)

    return workflow


async def get_workflows(
    session: AsyncSession,
) -> list[Workflow]:
    result = await session.scalars(
        select(Workflow).order_by(Workflow.created_at.desc())
    )

    return list(result.all())


async def get_workflow(
    session: AsyncSession,
    workflow_id: UUID,
) -> Workflow | None:
    result = await session.execute(select(Workflow).where(Workflow.id == workflow_id))

    return result.scalar_one_or_none()


async def update_workflow(
    session: AsyncSession,
    workflow_id: UUID,
    data: WorkflowUpdate,
) -> Workflow | None:
    workflow = await get_workflow(
        session=session,
        workflow_id=workflow_id,
    )

    if workflow is None:
        return None

    workflow.name = data.name
    workflow.description = data.description

    await session.commit()
    await session.refresh(workflow)

    return workflow
