FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    git \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
ARG TT_COMMON_REF=v0.1.17
RUN sed -i "s#@v[0-9][0-9.]*#@${TT_COMMON_REF}#" requirements.txt \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup --no-create-home appuser \
    && mkdir -p /app/instance/uploads && chown -R appuser:appgroup /app
USER appuser

ENV FLASK_APP=run.py
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Zurich

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "run:app"]
