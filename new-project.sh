#!/usr/bin/env bash
# =============================================================================
# new-project.sh — SaaS Boilerplate Project Initializer
# =============================================================================
# Usage: ./new-project.sh
# Interactively prompts for project details and creates a new project.
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_header() {
  echo ""
  echo -e "${BLUE}${BOLD}╔════════════════════════════════════════╗${NC}"
  echo -e "${BLUE}${BOLD}║       SaaS Boilerplate Initializer     ║${NC}"
  echo -e "${BLUE}${BOLD}╚════════════════════════════════════════╝${NC}"
  echo ""
}

print_step() {
  echo -e "${GREEN}${BOLD}▶ $1${NC}"
}

print_info() {
  echo -e "${YELLOW}  → $1${NC}"
}

print_error() {
  echo -e "${RED}${BOLD}✗ $1${NC}"
}

print_success() {
  echo -e "${GREEN}${BOLD}✓ $1${NC}"
}

ask() {
  local prompt="$1"
  local default="${2:-}"
  local value

  if [[ -n "$default" ]]; then
    read -r -p "$(echo -e "${BOLD}${prompt}${NC} [${default}]: ")" value
    echo "${value:-$default}"
  else
    read -r -p "$(echo -e "${BOLD}${prompt}${NC}: ")" value
    echo "$value"
  fi
}

ask_yes_no() {
  local prompt="$1"
  local default="${2:-y}"
  local value

  read -r -p "$(echo -e "${BOLD}${prompt}${NC} [${default}]: ")" value
  value="${value:-$default}"
  value="$(echo "$value" | tr '[:upper:]' '[:lower:]')"
  if [[ "$value" == "y" || "$value" == "yes" ]]; then
    YN_RESULT="true"
  else
    YN_RESULT="false"
  fi
}

generate_secret_key() {
  python3 -c "import secrets; print(secrets.token_urlsafe(64))"
}

# =============================================================================
# MAIN
# =============================================================================

print_header

echo -e "${BOLD}Let's set up your new SaaS project.${NC}"
echo -e "This script will copy the boilerplate and configure it for your project."
echo ""

# --- Collect project details ---
print_step "Project Details"

PROJECT_NAME=$(ask "Project name (snake_case, e.g. my_saas)" "my_saas")

# Validate: only lowercase letters, digits, and underscores
if [[ ! "$PROJECT_NAME" =~ ^[a-z][a-z0-9_]*$ ]]; then
  print_error "Project name must be lowercase letters, digits, and underscores only (no spaces, hyphens, or special chars)."
  exit 1
fi

PROJECT_DISPLAY_NAME=$(ask "Display name (e.g. My SaaS)" "My SaaS")
DOMAIN=$(ask "Production domain (e.g. myapp.com)" "myapp.com")
ADMIN_URL=$(ask "Django admin URL slug (e.g. admin-secret)" "admin-secret")

echo ""
print_step "Output Directory"
OUTPUT_DIR=$(ask "Create project in directory" "../${PROJECT_NAME}")
OUTPUT_DIR="${OUTPUT_DIR/#\~/$HOME}"  # Expand ~

# --- Feature flags ---
echo ""
print_step "Features to enable"
ask_yes_no "Enable team management?" "y"; ENABLE_TEAMS="$YN_RESULT"
ask_yes_no "Enable Stripe billing?" "y"; ENABLE_BILLING="$YN_RESULT"
ask_yes_no "Enable real-time notifications?" "y"; ENABLE_NOTIFICATIONS="$YN_RESULT"

# --- Confirm ---
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}Project Summary:${NC}"
echo -e "  Name:          ${GREEN}${PROJECT_NAME}${NC}"
echo -e "  Display:       ${GREEN}${PROJECT_DISPLAY_NAME}${NC}"
echo -e "  Domain:        ${GREEN}${DOMAIN}${NC}"
echo -e "  Admin URL:     ${GREEN}/${ADMIN_URL}/${NC}"
echo -e "  Output dir:    ${GREEN}${OUTPUT_DIR}${NC}"
echo -e "  Teams:         ${GREEN}${ENABLE_TEAMS}${NC}"
echo -e "  Billing:       ${GREEN}${ENABLE_BILLING}${NC}"
echo -e "  Notifications: ${GREEN}${ENABLE_NOTIFICATIONS}${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

ask_yes_no "Proceed?"; PROCEED="$YN_RESULT"
if [[ "$PROCEED" == "false" ]]; then
  echo "Aborted."
  exit 0
fi

# =============================================================================
# CREATE PROJECT
# =============================================================================

echo ""
print_step "Creating project directory..."

if [[ -d "$OUTPUT_DIR" ]]; then
  print_error "Directory already exists: $OUTPUT_DIR"
  ask_yes_no "Continue anyway (this may overwrite files)?"; OVERWRITE="$YN_RESULT"
  if [[ "$OVERWRITE" == "false" ]]; then
    exit 1
  fi
fi

mkdir -p "$OUTPUT_DIR"

# --- Copy boilerplate ---
print_step "Copying boilerplate..."

DIRS_TO_COPY=("backend" "frontend" "testing" ".github" "docs" "ops" "deploy" "scripts" "backup")

for dir in "${DIRS_TO_COPY[@]}"; do
  if [[ -d "${SCRIPT_DIR}/${dir}" ]]; then
    rsync -a \
      --exclude='.venv/' \
      --exclude='__pycache__/' \
      --exclude='*.pyc' \
      --exclude='*.pyo' \
      --exclude='.pytest_cache/' \
      --exclude='.ruff_cache/' \
      --exclude='htmlcov/' \
      --exclude='.coverage' \
      --exclude='node_modules/' \
      --exclude='.next/' \
      --exclude='*.tsbuildinfo' \
      --exclude='.pnpm-store/' \
      "${SCRIPT_DIR}/${dir}/" "${OUTPUT_DIR}/${dir}/"
    print_info "Copied ${dir}/"
  else
    print_info "Skipping ${dir}/ (not found)"
  fi
done

# Copy root-level files
ROOT_FILES=(".gitignore" "docker-compose.yml" "Makefile" "README.md" "CLAUDE.md" "SETUP.md" "RELEASE.md" "CHANGELOG.md" "BACKLOG.md" "SECURITY.md")
for file in "${ROOT_FILES[@]}"; do
  if [[ -f "${SCRIPT_DIR}/${file}" ]]; then
    cp "${SCRIPT_DIR}/${file}" "${OUTPUT_DIR}/${file}"
    print_info "Copied ${file}"
  fi
done

# --- Generate secret key ---
print_step "Generating Django secret key..."
SECRET_KEY=$(generate_secret_key)
print_success "Secret key generated"

# --- Replace placeholders ---
print_step "Configuring project..."

# Files to process for placeholder replacement
find "$OUTPUT_DIR" -type f \
  \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.json" \
     -o -name "*.toml" -o -name "*.yml" -o -name "*.yaml" -o -name "*.md" \
     -o -name "*.env.example" -o -name "*.sh" -o -name "Makefile" \
     -o -name "Procfile" -o -name "robots.txt" \) \
  ! -path "*/node_modules/*" \
  ! -path "*/.git/*" \
  ! -path "*/__pycache__/*" \
  ! -name "pnpm-lock.yaml" \
  -print0 | while IFS= read -r -d '' file; do
    sed -i.bak \
      -e "s|{{PROJECT_NAME}}|${PROJECT_NAME}|g" \
      -e "s|{{PROJECT_DISPLAY_NAME}}|${PROJECT_DISPLAY_NAME}|g" \
      -e "s|{{DOMAIN}}|${DOMAIN}|g" \
      -e "s|{{ADMIN_URL}}|${ADMIN_URL}|g" \
      -e "s|{{APP_NAME}}|${PROJECT_DISPLAY_NAME}|g" \
      -e "s|saas_boilerplate|${PROJECT_NAME}|g" \
      "$file" && rm -f "${file}.bak"
  done

print_success "Placeholders replaced"

# --- Create .env files ---
print_step "Creating .env files..."

# Backend .env
if [[ -f "${OUTPUT_DIR}/backend/.env.example" ]]; then
  cp "${OUTPUT_DIR}/backend/.env.example" "${OUTPUT_DIR}/backend/.env"

  # Fill in generated values
  sed -i.bak \
    -e "s|SECRET_KEY=change-me-generate-with-python-secrets|SECRET_KEY=${SECRET_KEY}|" \
    -e "s|DATABASE_URL=postgres://user:password@localhost:5432/dbname|DATABASE_URL=postgres://postgres@localhost:5432/${PROJECT_NAME}|" \
    -e "s|FEATURE_TEAMS=true|FEATURE_TEAMS=${ENABLE_TEAMS}|" \
    -e "s|FEATURE_BILLING=true|FEATURE_BILLING=${ENABLE_BILLING}|" \
    -e "s|FEATURE_NOTIFICATIONS=true|FEATURE_NOTIFICATIONS=${ENABLE_NOTIFICATIONS}|" \
    -e "s|DJANGO_SETTINGS_MODULE=config.settings.production|DJANGO_SETTINGS_MODULE=config.settings.development|" \
    -e "s|DEBUG=False|DEBUG=True|" \
    -e "s|APP_NAME=MyApp|APP_NAME=${PROJECT_DISPLAY_NAME}|" \
    -e "s|ADMIN_URL=tacomate|ADMIN_URL=${ADMIN_URL}|" \
    "${OUTPUT_DIR}/backend/.env" && rm -f "${OUTPUT_DIR}/backend/.env.bak"

  print_success "backend/.env created"
fi

# Frontend .env.local
if [[ -f "${OUTPUT_DIR}/frontend/.env.example" ]]; then
  cp "${OUTPUT_DIR}/frontend/.env.example" "${OUTPUT_DIR}/frontend/.env.local"

  sed -i.bak \
    -e "s|NEXT_PUBLIC_APP_NAME=MyApp|NEXT_PUBLIC_APP_NAME=${PROJECT_DISPLAY_NAME}|" \
    "${OUTPUT_DIR}/frontend/.env.local" && rm -f "${OUTPUT_DIR}/frontend/.env.local.bak"

  print_success "frontend/.env.local created"
fi

# Testing .env
if [[ -f "${OUTPUT_DIR}/testing/.env.example" ]]; then
  cp "${OUTPUT_DIR}/testing/.env.example" "${OUTPUT_DIR}/testing/.env"
  print_success "testing/.env created"
fi

# --- Update Makefile ---
if [[ -f "${OUTPUT_DIR}/backend/Makefile" ]]; then
  sed -i.bak "s|PROJECT_NAME ?= saas_boilerplate|PROJECT_NAME ?= ${PROJECT_NAME}|" \
    "${OUTPUT_DIR}/backend/Makefile" && rm -f "${OUTPUT_DIR}/backend/Makefile.bak"
fi

# --- Initialize git ---
print_step "Initializing git repository..."
cd "$OUTPUT_DIR"
git init -q
git add -A -- ':!backend/.env' ':!frontend/.env.local' ':!testing/.env'
git commit -q -m "chore: initial commit from saas-boilerplate

Project: ${PROJECT_NAME}
Domain: ${DOMAIN}"
print_success "Git repository initialized with initial commit"

# =============================================================================
# NEXT STEPS
# =============================================================================

echo ""
echo -e "${BLUE}${BOLD}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}${BOLD}║              🎉 Project Created Successfully!          ║${NC}"
echo -e "${BLUE}${BOLD}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BOLD}Project location:${NC} ${OUTPUT_DIR}"
echo ""
echo -e "${BOLD}━━━ Next Steps ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BOLD}1. Backend setup${NC}"
echo -e "   cd ${OUTPUT_DIR}/backend"
echo -e "   uv sync                          # Install dependencies"
echo -e "   ${YELLOW}# Edit .env with your API keys${NC}"
echo -e "   make db-create                   # Create PostgreSQL database"
echo -e "   make migrate                     # Run migrations"
echo -e "   make seed                        # Create sample data"
echo -e "   make run                         # Start server (port 8000)"
echo -e "   make worker                      # Start Celery worker (new terminal)"
echo ""
echo -e "${BOLD}2. Frontend setup${NC}"
echo -e "   cd ${OUTPUT_DIR}/frontend"
echo -e "   pnpm install                     # Install dependencies"
echo -e "   ${YELLOW}# Edit .env.local with your keys${NC}"
echo -e "   pnpm dev                         # Start dev server (port 3000)"
echo ""
echo -e "${BOLD}3. E2E tests${NC}"
echo -e "   cd ${OUTPUT_DIR}/testing"
echo -e "   pnpm install"
echo -e "   pnpm run install:browsers"
echo -e "   pnpm test"
echo ""
echo -e "${BOLD}━━━ Required API Keys ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${YELLOW}□${NC} Stripe:       STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET"
echo -e "  ${YELLOW}□${NC} Google OAuth: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET"
echo -e "  ${YELLOW}□${NC} Resend:       RESEND_API_KEY"
echo -e "  ${YELLOW}□${NC} Sentry:       SENTRY_DSN (optional)"
echo ""
echo -e "${BOLD}━━━ Documentation ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  Deployment:   ${OUTPUT_DIR}/ops/KAMAL_SETUP.md"
echo -e "  Architecture: ${OUTPUT_DIR}/docs/ARCHITECTURE.md"
echo -e "  Decisions:    ${OUTPUT_DIR}/docs/DECISIONS.md"
echo -e "  Launch:       ${OUTPUT_DIR}/ops/LAUNCH_CHECKLIST.md"
echo ""
echo -e "${BOLD}━━━ Multi-tenancy (local dev) ━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  Add to /etc/hosts for subdomain testing:"
echo -e "  ${YELLOW}127.0.0.1 test-company.localhost${NC}"
echo ""
echo -e "Happy building! 🚀"
echo ""
