import graphlib
import typing
from contextlib import asynccontextmanager

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic import BaseSettings


class Settings(BaseSettings):
    tasks: str = "tasks.yml"
    builds: str = "builds.yml"


class Build(BaseModel):
    build: str


class Tasks(BaseModel):
    tasks: typing.List[str]


settings = Settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    with open(settings.tasks, "r") as file:
        tasks = yaml.safe_load(file)
        _app.tasks = {
            task["name"]: task
            for task in tasks["tasks"]
        }

    with open(settings.builds, "r") as file:
        builds = yaml.safe_load(file)
        _app.builds = {
            build["name"]: build
            for build in builds["builds"]
        }
    yield


app = FastAPI(lifespan=lifespan)


def get_dependencies(task_name, tasks, sorter):
    sorter.add(task_name, *tasks[task_name]["dependencies"])
    for dep in tasks[task_name]["dependencies"]:
        get_dependencies(dep, tasks, sorter)


@app.post("/get_tasks")
async def get_tasks(build: Build) -> Tasks:
    try:
        build_data = app.builds[build.build]
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Build with name {build.build} not found")

    sorter = graphlib.TopologicalSorter()
    sorter.add(build_data["name"], *build_data["tasks"])

    try:
        for dep in build_data["tasks"]:
            get_dependencies(dep, app.tasks, sorter)
    except KeyError as exc:
        missing_key, *_ = exc.args
        raise HTTPException(status_code=400, detail=f"Task with name {missing_key} not found")

    return Tasks(tasks=list(sorter.static_order())[:-1])  # последним элементом всегда будет название билда
