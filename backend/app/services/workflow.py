from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.infrastructure.models.workflow import Workflow
from backend.app.schemas.workflow import WorkflowCreate


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
