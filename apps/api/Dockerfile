FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/api ./apps/api
COPY database ./database
COPY alembic.ini .
ENV PYTHONPATH=/app/apps/api
RUN useradd --create-home app && chown -R app:app /app
USER app
CMD ["sh","-c","python -m alembic upgrade head && python -m uvicorn covenantx.main:app --host 0.0.0.0 --port 8000"]
