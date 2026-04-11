FROM python:3.12-slim

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -e ".[redis]"

ENV PORT=3302
EXPOSE 3302

CMD polyclash serve --no-auth --host 0.0.0.0 --port $PORT
