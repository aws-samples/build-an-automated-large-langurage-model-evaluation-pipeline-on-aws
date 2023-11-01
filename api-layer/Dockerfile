FROM python:3.10-slim

RUN python3 -m pip install uvicorn fastapi -U -q
WORKDIR /code/app
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app

ENTRYPOINT ["python3", "/code/app/main.py"] 
