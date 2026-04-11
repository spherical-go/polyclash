FROM python:3.12-slim

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -e ".[redis]"

ENV PORT=3302
ENV POLYCLASH_MAX_ROOMS=8
ENV POLYCLASH_INVITES=5

EXPOSE 3302

# Default: team mode — all config via env vars
CMD ["polyclash", "team"]
