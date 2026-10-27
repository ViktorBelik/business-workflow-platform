import pytest
from httpx2 import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.infrastructure.models.workflow import Workflow


@pytest.mark.asyncio
async def test_create_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    response = await client.post(
        "/workflows",
        json={
            "name": "Обработка заявки клиента",
            "description": "Автоматическая обработка входящих заявок",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Обработка заявки клиента"
    assert data["description"] == "Автоматическая обработка входящих заявок"
    assert data["status"] == "active"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

    result = await db_session.execute(
        select(Workflow).where(Workflow.name == "Обработка заявки клиента")
    )
    workflow = result.scalar_one()

    assert str(workflow.id) == data["id"]
    assert workflow.description == data["description"]


@pytest.mark.asyncio
async def test_get_workflows(
    client: AsyncClient,
) -> None:
    first_response = await client.post(
        "/workflows",
        json={"name": "Первый процесс"},
    )
    second_response = await client.post(
        "/workflows",
        json={"name": "Второй процесс"},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = await client.get("/workflows")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["name"] == "Первый процесс"
    assert data[1]["name"] == "Второй процесс"


@pytest.mark.asyncio
async def test_get_workflows_empty(
    client: AsyncClient,
) -> None:
    response = await client.get("/workflows")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_workflow(
    client: AsyncClient,
) -> None:
    create_response = await client.post(
        "/workflows",
        json={
            "name": "Обработка заказа",
            "description": "Автоматизация обработки заказа",
        },
    )

    assert create_response.status_code == 201

    created_workflow = create_response.json()
    workflow_id = created_workflow["id"]

    response = await client.get(f"/workflows/{workflow_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == workflow_id
    assert data["name"] == "Обработка заказа"
    assert data["description"] == "Автоматизация обработки заказа"
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_get_workflow_not_found(
    client: AsyncClient,
) -> None:
    workflow_id = "00000000-0000-0000-0000-000000000001"

    response = await client.get(f"/workflows/{workflow_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Workflow not found"}
