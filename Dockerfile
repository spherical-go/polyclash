FROM python:3.12-slim

WORKDIR /app

# Install only server dependencies (no Qt/VTK)
COPY requirements.txt .
RUN grep -vE "PyQt5|pyvista" requirements.txt > requirements-server.txt && \
    pip install --no-cache-dir -r requirements-server.txt

COPY . .
RUN pip install --no-cache-dir -e . --no-deps

EXPOSE 3302

CMD ["polyclash", "serve", "--host", "0.0.0.0", "--port", "3302"]
