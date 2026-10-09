FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd --uid 10001 --create-home app && mkdir /data && chown app:app /data
COPY --chown=app:app . .
USER app
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "120", "--access-logfile", "-", "--access-logformat", "%(h)s %(s)s %(b)s %(L)s"]
