from celery import group
from fastapi import APIRouter
from starlette.responses import JSONResponse

from celery_tasks.tasks import get_run_task, get_logging_task
from config.celery_utils import get_task_info

router = APIRouter(prefix='', tags=['Training'], responses={404: {"description": "Not found"}})


@router.post("/run")
async def get_run() -> dict:
    """
    Return the List of universities for the countries for e.g ["turkey","india","australia"] provided
    in input in a sync way
    """
    task = get_run_task.apply_async()
    return JSONResponse({"task_id": task.id})


@router.post("/logging")
async def get_logging() -> dict:
    """
    Return the List of universities for the countries for e.g ["turkey","india","australia"] provided
    in input in a sync way
    """
    task = get_logging_task.apply_async()
    return JSONResponse({"task_id": task.id})


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str) -> dict:
    """
    Return the status of the submitted Task
    """
    return get_task_info(task_id)

