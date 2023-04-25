from fastapi.testclient import TestClient

from app import app

builds = {
    "ok_build":
        {
            "name": "ok_build",
            "tasks": ["task4", "task3", "task2"],

        },
    "broken_build":
        {
            "name": "broken_build",
            "tasks": ["unknown_task"],
        }

}

tasks = {
    "task1": {
        "name": "task1",
        "dependencies": set()
    },
    "task2": {
        "name": "task2",
        "dependencies": {"task1"}
    },
    "task3": {
        "name": "task3",
        "dependencies": {"task1"}
    },
    "task4": {
        "name": "task4",
        "dependencies": {"task2", "task3"}
    },
}
app.builds = builds
app.tasks = tasks
client = TestClient(app)

expected_build_result = ["task1", "task3", "task2", "task4"]


def test_build():
    response = client.post("/get_tasks", json={"build": "ok_build"})
    assert response.status_code == 200
    assert response.json()["tasks"] == expected_build_result


def test_build_not_found():
    response = client.post("/get_tasks", json={"build": "unknown_build_name"})
    assert response.status_code == 404


def test_broken_build():
    response = client.post("/get_tasks", json={"build": "broken_build"})
    assert response.status_code == 400
