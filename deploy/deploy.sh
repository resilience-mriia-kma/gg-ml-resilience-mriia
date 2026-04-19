#!/bin/bash
set -e

PROJECT_DIR="/opt/mriia"
CODE_DIR="$PROJECT_DIR/code"

pull_code() {
    echo "Pulling latest code..."
    cd "$CODE_DIR"
    git fetch origin main
    git reset --hard origin/main
}

install_dependencies() {
    echo "Installing dependencies..."
    cd "$CODE_DIR"
    source .venv/bin/activate
    uv pip install -r pyproject.toml
}

run_migrations() {
    echo "Running database migrations..."
    cd "$CODE_DIR"
    source .venv/bin/activate
    python manage.py migrate --no-input
}

collect_static() {
    echo "Collecting static files..."
    cd "$CODE_DIR"
    source .venv/bin/activate
    python manage.py collectstatic --no-input
}

restart_services() {
    echo "Restarting services..."
    sudo systemctl restart ml-resilience-gunicorn
    sudo systemctl restart nginx
}

check_services() {
    echo "Checking service status..."
    sudo systemctl is-active ml-resilience-gunicorn
    sudo systemctl is-active nginx
}

main() {
    echo "Starting deployment..."

    pull_code
    install_dependencies
    run_migrations
    collect_static
    restart_services
    check_services

    echo "Deployment completed successfully!"
}

main "$@"
