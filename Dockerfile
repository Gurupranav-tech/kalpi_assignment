FROM python:3.11-slim

RUN apt-get update && apt-get install -y build-essential

WORKDIR /app

COPY Pipfile .

COPY Pipfile.lock .

RUN pip install pipenv

RUN pipenv install --deploy --system

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
