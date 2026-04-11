FROM python:3.12-slim

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -e ".[redis]"

# Persistent volume for user database
VOLUME ["/data"]

ENV PORT=3302
ENV POLYCLASH_AUTH_DB=/data/polyclash_users.db
ENV POLYCLASH_MAX_ROOMS=8
ENV POLYCLASH_INVITES=5

EXPOSE 3302

# Default: team mode — all config via env vars
CMD ["polyclash", "team"]
