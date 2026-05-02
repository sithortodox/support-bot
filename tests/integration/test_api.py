import pytest
from httpx import AsyncClient

class TestAPIEndpoints:
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "Support Bot API" in data["service"]
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

class TestAnalyticsEndpoints:
    @pytest.mark.asyncio
    async def test_get_ai_analytics(self, client: AsyncClient):
        response = await client.get("/api/v1/analytics/ai?hours=24")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_requests" in data
        assert "total_tokens" in data
        assert "estimated_cost" in data
    
    @pytest.mark.asyncio
    async def test_get_satisfaction_analytics(self, client: AsyncClient):
        response = await client.get("/api/v1/analytics/satisfaction?hours=24")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_ratings" in data
        assert "positive" in data
        assert "negative" in data
    
    @pytest.mark.asyncio
    async def test_get_category_distribution(self, client: AsyncClient):
        response = await client.get("/api/v1/analytics/categories?hours=168")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "categories" in data
        assert "total" in data
    
    @pytest.mark.asyncio
    async def test_get_sentiment_distribution(self, client: AsyncClient):
        response = await client.get("/api/v1/analytics/sentiment?hours=168")
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_hourly_activity(self, client: AsyncClient):
        response = await client.get("/api/v1/analytics/activity?hours=168")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_get_dashboard_data(self, client: AsyncClient):
        response = await client.get("/api/v1/analytics/dashboard?hours=24")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "ai" in data
        assert "satisfaction" in data
        assert "categories" in data
        assert "sentiment" in data
        assert "activity" in data
        assert "tickets" in data

class TestExportEndpoint:
    @pytest.mark.asyncio
    async def test_export_tickets_csv(self, client: AsyncClient):
        response = await client.get("/api/v1/analytics/export/tickets?hours=720")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]

class TestDashboardEndpoint:
    @pytest.mark.asyncio
    async def test_dashboard_html(self, client: AsyncClient):
        response = await client.get("/dashboard")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
