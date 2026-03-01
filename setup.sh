#!/usr/bin/env bash
# Banking App — one-command Docker setup (Linux / macOS / Git Bash on Windows)
set -e

echo "=== Banking App Setup ==="

# Check Docker is available
if ! command -v docker &> /dev/null; then
  echo "Error: Docker is not installed or not in PATH."
  exit 1
fi

# Create .env from example if it doesn't exist
if [ ! -f .env ]; then
  cp .env.example .env
  # Generate a random JWT secret
  SECRET=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/change-me-generate-with-openssl-rand-hex-32/$SECRET/" .env
  else
    sed -i "s/change-me-generate-with-openssl-rand-hex-32/$SECRET/" .env
  fi
  echo "Created .env with generated JWT secret."
else
  echo ".env already exists, skipping."
fi

# Build and start
echo "Building and starting containers..."
docker compose up --build -d

echo ""
echo "=== Setup complete ==="
echo "App running at: http://localhost:8000"
echo "API docs at:    http://localhost:8000/docs"
echo ""
echo "To stop:  docker compose down"
echo "To logs:  docker compose logs -f"
