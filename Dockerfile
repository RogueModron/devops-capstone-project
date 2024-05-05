FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install -U pip wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY service ./service

RUN useradd -r theia && \
    chown -R theia:theia /app
USER theia

ENV PORT 8080
EXPOSE $PORT
CMD ["gunicorn", "service:app", "--bind", "0.0.0.0:8080", "--log-level", "info"]