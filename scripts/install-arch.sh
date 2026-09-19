#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# V-Scan — (Arch)Linux Setup Script
# Run once as a regular user with sudo privileges.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]  ${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }

# ── 1. System update ──────────────────────────────────────────────────────────
info "Updating system packages..."
sudo pacman -Syu --noconfirm

# ── 2. Install Docker & Docker Compose ───────────────────────────────────────
info "Installing Docker and Docker Compose..."
sudo pacman -S --noconfirm docker docker-compose

# ── 3. Enable & start Docker daemon ──────────────────────────────────────────
info "Enabling Docker service..."
sudo systemctl enable --now docker
success "Docker daemon started."

# ── 4. Add current user to docker group ──────────────────────────────────────
if ! groups "$USER" | grep -q docker; then
    info "Adding $USER to 'docker' group..."
    sudo usermod -aG docker "$USER"
    warn "You must log out and back in for group changes to take effect."
    warn "Or run: newgrp docker"
else
    success "$USER is already in the 'docker' group."
fi

# ── 5. Optional: Python for local dev ────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    info "Installing Python 3 and pip..."
    sudo pacman -S --noconfirm python python-pip
fi

# ── 6. Verify Docker works ────────────────────────────────────────────────────
info "Verifying Docker installation..."
if sudo docker run --rm hello-world &>/dev/null; then
    success "Docker is working correctly."
else
    warn "Docker test failed. Check 'sudo systemctl status docker'."
fi

# ── 7. Build and start V-Scan ─────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

info "Building V-Scan Docker images..."
cd "$PROJECT_DIR"
docker compose build

info "Starting V-Scan services..."
docker compose up -d

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  V-Scan is ready!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Run a scan:"
echo "    docker compose exec scanner-app python src/main.py \\"
echo "      --url https://example.com \\"
echo "      --questionnaire questionnaire.json"
echo ""
echo "  View dashboard: http://localhost:3000  (admin / admin)"
echo ""
