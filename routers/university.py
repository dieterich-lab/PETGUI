from celery import group
from fastapi import APIRouter
from starlette.responses import JSONResponse

import universities
from celery_tasks.tasks import get_university_task
from config.celery_utils import get_task_info

router = APIRouter(prefix='/university', tags=['university'], responses={404: {"description": "Not found"}})
uni = universities.API()

@router.post("/")
def get_university(country: str) -> dict:
    """
    Return the List of universities for the countries for e.g ["turkey","india","australia"] provided
    in input in a sync way
    """
    data: dict = {}
    data[country] = list(uni.search(country=country))
    return None


@router.post("/async")
async def get_university_async(country: str):
    """
    Return the List of universities for the countries for e.g ["turkey","india","australia"] provided
    in input in a async way. It just returns the task id, which can later be used to get the result.
    """
    task = get_university_task.apply_async(country=country)
    return JSONResponse({"task_id": task.id})


@router.get("/task/{task_id}")
async def get_task_status(task_id: str) -> dict:
    """
    Return the status of the submitted Task
    """
    return get_task_info(task_id)


@router.post("/parallel")
async def get_university_parallel(country: str) -> dict:
    """
    Return the List of universities for the countries for e.g ["turkey","india","australia"] provided
    in input in a sync way. This will use Celery to perform the subtasks in a parallel manner
    """

    data: dict = {}
    tasks = []
    tasks.append(get_university_task.s(country))
    # create a group with all the tasks
    job = group(tasks)
    result = job.apply_async()
    ret_values = result.get(disable_sync_subtasks=False)
    for result in ret_values:
        data.update(result)
    return data
