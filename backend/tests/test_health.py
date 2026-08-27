import asyncio

from httpx import ASGITransport, AsyncClient, Response

from app.main import app


async def request_health() -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get("/api/v1/health")


async def request_delete_preflight() -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.options(
            "/api/v1/analysis-cases/00000000-0000-0000-0000-000000000000/documents/"
            "00000000-0000-0000-0000-000000000000",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "DELETE",
                "Access-Control-Request-Headers": "X-User-Id",
            },
        )


def test_health() -> None:
    response = asyncio.run(request_health())

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_cors_allows_document_deletion_preflight() -> None:
    response = asyncio.run(request_delete_preflight())

    assert response.status_code == 200
    assert "DELETE" in response.headers["access-control-allow-methods"]
