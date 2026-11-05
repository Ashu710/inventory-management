"""
Tests for tasks and purchase order API endpoints.
"""


class TestTasksEndpoints:
    """Test suite for task CRUD endpoints."""

    def _create(self, client, **overrides):
        payload = {"title": "Review stock", "priority": "high", "dueDate": "2025-12-01", **overrides}
        return client.post("/api/tasks", json=payload)

    def test_get_all_tasks_empty(self, client):
        """Test that tasks start empty."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        """Test creating a task returns it as pending with a string id."""
        response = self._create(client)
        assert response.status_code == 201

        task = response.json()
        assert task["title"] == "Review stock"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2025-12-01"
        assert task["status"] == "pending"
        # String ids keep API tasks distinct from the client's integer-id demo tasks
        assert isinstance(task["id"], str)

    def test_created_tasks_listed_newest_first(self, client):
        """Test that new tasks appear at the start of the list."""
        first = self._create(client, title="First").json()
        second = self._create(client, title="Second").json()

        data = client.get("/api/tasks").json()
        assert [t["id"] for t in data] == [second["id"], first["id"]]

    def test_create_task_invalid_priority(self, client):
        """Test that an unknown priority is rejected."""
        response = self._create(client, priority="urgent")
        assert response.status_code == 422

    def test_create_task_empty_title(self, client):
        """Test that an empty title is rejected."""
        response = self._create(client, title="")
        assert response.status_code == 422

    def test_toggle_task(self, client):
        """Test toggling flips status both ways."""
        task_id = self._create(client).json()["id"]

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.json()["status"] == "pending"

    def test_delete_task(self, client):
        """Test deleting a task removes it."""
        task_id = self._create(client).json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert client.get("/api/tasks").json() == []

    def test_toggle_nonexistent_task(self, client):
        """Test toggling a missing task returns 404."""
        response = client.patch("/api/tasks/task-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_nonexistent_task(self, client):
        """Test deleting a missing task returns 404."""
        response = client.delete("/api/tasks/task-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestPurchaseOrderEndpoints:
    """Test suite for purchase order endpoints."""

    def _backlog_item(self, client):
        items = client.get("/api/backlog").json()
        assert len(items) > 0
        return items[0]

    def _payload(self, backlog_item_id, **overrides):
        return {
            "backlog_item_id": backlog_item_id,
            "supplier_name": "Acme Supply",
            "quantity": 100,
            "unit_cost": 12.5,
            "expected_delivery_date": "2025-12-15",
            "notes": "Rush",
            **overrides,
        }

    def test_backlog_items_have_no_po_initially(self, client):
        """Test backlog items expose purchase_order_id as null before any PO."""
        for item in client.get("/api/backlog").json():
            assert item["has_purchase_order"] is False
            assert item["purchase_order_id"] is None

    def test_create_purchase_order(self, client):
        """Test creating a PO returns it with server-set fields."""
        item = self._backlog_item(client)
        response = client.post("/api/purchase-orders", json=self._payload(item["id"]))
        assert response.status_code == 201

        po = response.json()
        assert po["id"].startswith("PO-")
        assert po["backlog_item_id"] == item["id"]
        assert po["supplier_name"] == "Acme Supply"
        assert po["quantity"] == 100
        assert abs(po["unit_cost"] - 12.5) < 0.01
        assert po["status"] == "Pending"
        assert "T" in po["created_date"]

    def test_backlog_reflects_created_purchase_order(self, client):
        """Test the backlog item links to its PO after creation."""
        item = self._backlog_item(client)
        po = client.post("/api/purchase-orders", json=self._payload(item["id"])).json()

        updated = next(b for b in client.get("/api/backlog").json() if b["id"] == item["id"])
        assert updated["has_purchase_order"] is True
        assert updated["purchase_order_id"] == po["id"]

    def test_get_purchase_order_by_backlog_item(self, client):
        """Test fetching a PO by its backlog item id."""
        item = self._backlog_item(client)
        created = client.post("/api/purchase-orders", json=self._payload(item["id"])).json()

        response = client.get(f"/api/purchase-orders/{item['id']}")
        assert response.status_code == 200
        assert response.json() == created

    def test_get_nonexistent_purchase_order(self, client):
        """Test fetching a PO for a backlog item without one returns 404."""
        item = self._backlog_item(client)
        response = client.get(f"/api/purchase-orders/{item['id']}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_duplicate_purchase_order(self, client):
        """Test a second PO for the same backlog item is rejected."""
        item = self._backlog_item(client)
        client.post("/api/purchase-orders", json=self._payload(item["id"]))

        response = client.post("/api/purchase-orders", json=self._payload(item["id"]))
        assert response.status_code == 409

    def test_create_purchase_order_unknown_backlog_item(self, client):
        """Test creating a PO for a missing backlog item returns 404."""
        response = client.post("/api/purchase-orders", json=self._payload("nonexistent-999"))
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_purchase_order_invalid_quantity(self, client):
        """Test zero quantity is rejected."""
        item = self._backlog_item(client)
        response = client.post("/api/purchase-orders", json=self._payload(item["id"], quantity=0))
        assert response.status_code == 400
