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

    data = response.json()["items"]

    assert len(data) == 2
    assert data[0]["name"] == "Первый процесс"
    assert data[1]["name"] == "Второй процесс"


@pytest.mark.asyncio
async def test_get_workflows_empty(
    client: AsyncClient,
) -> None:
    response = await client.get("/workflows")

    assert response.status_code == 200
    assert response.json()["items"] == []


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


@pytest.mark.asyncio
async def test_update_workflow(
    client: AsyncClient,
) -> None:
    create_response = await client.post(
        "/workflows",
        json={
            "name": "Исходный процесс",
            "description": "Исходное описание",
        },
    )

    assert create_response.status_code == 201

    created_workflow = create_response.json()

    workflow_id = created_workflow["id"]
    created_at = created_workflow["created_at"]

    update_response = await client.put(
        f"/workflows/{workflow_id}",
        json={
            "name": "Обновлённый процесс",
            "description": "Обновлённое описание",
        },
    )

    assert update_response.status_code == 200

    data = update_response.json()

    assert data["id"] == workflow_id
    assert data["name"] == "Обновлённый процесс"
    assert data["description"] == "Обновлённое описание"
    assert data["status"] == "active"
    assert data["created_at"] == created_at
    assert data["updated_at"] != created_at


@pytest.mark.asyncio
async def test_update_workflow_not_found(
    client: AsyncClient,
) -> None:
    workflow_id = "00000000-0000-0000-0000-000000000001"

    response = await client.put(
        f"/workflows/{workflow_id}",
        json={
            "name": "Обновлённый процесс",
            "description": "Обновлённое описание",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workflow not found"}


@pytest.mark.asyncio
async def test_deactivate_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    create_response = await client.post(
        "/workflows",
        json={
            "name": "Процесс для деактивации",
            "description": "Проверка мягкого удаления",
        },
    )

    assert create_response.status_code == 201

    created_workflow = create_response.json()
    workflow_id = created_workflow["id"]

    response = await client.delete(f"/workflows/{workflow_id}")

    assert response.status_code == 204
    assert response.content == b""

    result = await db_session.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one()

    assert workflow.status == "inactive"


@pytest.mark.asyncio
async def test_deactivate_workflow_not_found(
    client: AsyncClient,
) -> None:
    workflow_id = "00000000-0000-0000-0000-000000000001"

    response = await client.delete(f"/workflows/{workflow_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Workflow not found"}


@pytest.mark.asyncio
async def test_deactivate_workflow_twice(
    client: AsyncClient,
) -> None:
    create_response = await client.post(
        "/workflows",
        json={"name": "Повторная деактивация"},
    )

    assert create_response.status_code == 201

    workflow_id = create_response.json()["id"]

    first_response = await client.delete(f"/workflows/{workflow_id}")
    second_response = await client.delete(f"/workflows/{workflow_id}")

    assert first_response.status_code == 204
    assert second_response.status_code == 204


@pytest.mark.asyncio
async def test_get_workflows_by_status(
    client: AsyncClient,
) -> None:
    active_response = await client.post(
        "/workflows",
        json={"name": "Активный процесс"},
    )
    inactive_response = await client.post(
        "/workflows",
        json={"name": "Неактивный процесс"},
    )

    assert active_response.status_code == 201
    assert inactive_response.status_code == 201

    inactive_id = inactive_response.json()["id"]

    deactivate_response = await client.delete(f"/workflows/{inactive_id}")
    assert deactivate_response.status_code == 204

    active_list_response = await client.get(
        "/workflows",
        params={"status": "active"},
    )
    inactive_list_response = await client.get(
        "/workflows",
        params={"status": "inactive"},
    )

    assert active_list_response.status_code == 200
    assert inactive_list_response.status_code == 200

    active_workflows = active_list_response.json()["items"]
    inactive_workflows = inactive_list_response.json()["items"]

    assert len(active_workflows) == 1
    assert active_workflows[0]["name"] == "Активный процесс"
    assert active_workflows[0]["status"] == "active"

    assert len(inactive_workflows) == 1
    assert inactive_workflows[0]["name"] == "Неактивный процесс"
    assert inactive_workflows[0]["status"] == "inactive"


@pytest.mark.asyncio
async def test_get_workflows_invalid_status(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/workflows",
        params={"status": "unknown"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_workflows_with_limit(client: AsyncClient) -> None:
    for name in ("Workflow 1", "Workflow 2", "Workflow 3"):
        await client.post(
            "/workflows",
            json={"name": name, "description": None},
        )

    response = await client.get("/workflows?limit=2")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


@pytest.mark.asyncio
async def test_get_workflows_with_offset(client: AsyncClient) -> None:
    for name in ("Workflow 1", "Workflow 2", "Workflow 3"):
        await client.post(
            "/workflows",
            json={"name": name, "description": None},
        )

    all_response = await client.get("/workflows")
    offset_response = await client.get("/workflows?offset=2")

    assert all_response.status_code == 200
    assert offset_response.status_code == 200

    all_workflows = all_response.json()["items"]
    offset_workflows = offset_response.json()["items"]

    assert len(all_workflows) == 3
    assert len(offset_workflows) == 1
    assert offset_workflows[0]["id"] == all_workflows[2]["id"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
    ],
)
async def test_get_workflows_invalid_pagination(
    client: AsyncClient,
    params: dict[str, int],
) -> None:
    response = await client.get("/workflows", params=params)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_workflows_status_with_limit(
    client: AsyncClient,
) -> None:
    await client.post(
        "/workflows",
        json={"name": "Active 1", "description": None},
    )
    await client.post(
        "/workflows",
        json={"name": "Active 2", "description": None},
    )

    response = await client.get("/workflows?status=active&limit=1")

    assert response.status_code == 200

    workflows = response.json()["items"]
    assert len(workflows) == 1
    assert workflows[0]["status"] == "active"


@pytest.mark.asyncio
async def test_get_workflows_pagination_metadata(
    client: AsyncClient,
) -> None:
    for name in ("Workflow 1", "Workflow 2", "Workflow 3"):
        await client.post(
            "/workflows",
            json={"name": name, "description": None},
        )

    response = await client.get("/workflows?limit=2&offset=1")

    assert response.status_code == 200

    data = response.json()

    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 1


@pytest.mark.asyncio
async def test_get_workflows_total_with_status_filter(
    client: AsyncClient,
) -> None:
    await client.post(
        "/workflows",
        json={"name": "Active 1", "description": None},
    )
    await client.post(
        "/workflows",
        json={"name": "Active 2", "description": None},
    )

    response = await client.get("/workflows?status=active&limit=1")

    assert response.status_code == 200

    data = response.json()

    assert len(data["items"]) == 1
    assert data["total"] == 2
    assert data["limit"] == 1
    assert data["offset"] == 0
