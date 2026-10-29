FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
RUN .venv/bin/python manage.py collectstatic --noinput \
    && useradd --uid 10001 --create-home reviewer \
    && mkdir -p /app/private-data \
    && chown -R reviewer:reviewer /app/private-data
USER reviewer
EXPOSE 8000
CMD [".venv/bin/gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "--access-logfile", "-"]
