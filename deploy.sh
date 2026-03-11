# Phase 8.3: Deployment Scripts
# =============================
# Deployment automation script for production

#!/bin/bash

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Flashcard Learning System - Production Deployment${NC}"
echo "=================================================="

# Function to print colored output
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're running as root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run this script as root or with sudo"
    exit 1
fi

# Configuration
DOMAIN_NAME=${1:-"yourdomain.com"}
EMAIL=${2:-"admin@$DOMAIN_NAME"}
PROJECT_DIR="/opt/flashcard-learning"
DOCKER_COMPOSE_VERSION="v2.23.3"

log_info "Domain: $DOMAIN_NAME"
log_info "Email: $EMAIL"
log_info "Project Directory: $PROJECT_DIR"

# Update system packages
log_info "Updating system packages..."
apt update && apt upgrade -y
log_success "System packages updated"

# Install required packages
log_info "Installing required packages..."
apt install -y \
    curl \
    wget \
    gnupg \
    lsb-release \
    ca-certificates \
    software-properties-common \
    ufw \
    fail2ban \
    certbot \
    python3-certbot-nginx
log_success "Required packages installed"

# Install Docker
log_info "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io
    log_success "Docker installed"
else
    log_success "Docker already installed"
fi

# Install Docker Compose
log_info "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/download/$DOCKER_COMPOSE_VERSION/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    log_success "Docker Compose installed"
else
    log_success "Docker Compose already installed"
fi

# Configure firewall
log_info "Configuring UFW firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
log_success "Firewall configured"

# Configure fail2ban
log_info "Configuring fail2ban..."
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
EOF

systemctl enable fail2ban
systemctl restart fail2ban
log_success "Fail2ban configured"

# Create project directory
log_info "Creating project directory..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR
log_success "Project directory created"

# Clone or update project (assuming Git repository)
log_info "Setting up project files..."
if [ -d ".git" ]; then
    git pull origin main
    log_success "Project updated from Git"
else
    log_warning "Git repository not found. Please manually copy your project files to $PROJECT_DIR"
    log_info "Required files: docker-compose.yml, nginx.conf, backend/.env.production"
fi

# Generate SSL certificate with Let's Encrypt
log_info "Generating SSL certificate with Let's Encrypt..."
if [ ! -f "/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem" ]; then
    # First, start nginx temporarily for HTTP-01 challenge
    docker run --rm -d \
        --name nginx-temp \
        -p 80:80 \
        -v /etc/letsencrypt:/etc/letsencrypt \
        -v /var/lib/letsencrypt:/var/lib/letsencrypt \
        nginx:alpine
    
    # Generate certificate
    certbot certonly \
        --webroot \
        --webroot-path=/var/lib/letsencrypt \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN_NAME \
        -d www.$DOMAIN_NAME
    
    # Stop temporary nginx
    docker stop nginx-temp
    
    log_success "SSL certificate generated"
else
    log_success "SSL certificate already exists"
fi

# Setup certificate renewal
log_info "Setting up SSL certificate auto-renewal..."
cat > /etc/systemd/system/certbot-renew.service << EOF
[Unit]
Description=Let's Encrypt renewal

[Service]
Type=oneshot
ExecStart=/usr/bin/certbot renew --quiet --deploy-hook "docker-compose -f $PROJECT_DIR/docker-compose.yml restart nginx"
EOF

cat > /etc/systemd/system/certbot-renew.timer << EOF
[Unit]
Description=Twice daily renewal of Let's Encrypt's certificates

[Timer]
OnCalendar=0/12:00:00
RandomizedDelaySec=1h
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl enable certbot-renew.timer
systemctl start certbot-renew.timer
log_success "SSL auto-renewal configured"

# Update nginx configuration with domain name
log_info "Updating nginx configuration..."
sed -i "s/yourdomain.com/$DOMAIN_NAME/g" nginx.conf
log_success "Nginx configuration updated"

# Create production environment file if it doesn't exist
if [ ! -f "backend/.env.production" ]; then
    log_warning "Production environment file not found. Creating template..."
    mkdir -p backend
    cat > backend/.env.production << EOF
# Production Environment Configuration
# Please update these values for your deployment

DATABASE_URL=postgresql://flashcard_user:$(openssl rand -base64 32)@postgres:5432/flashcard_production
SECRET_KEY=$(openssl rand -base64 32)
CORS_ORIGINS=https://$DOMAIN_NAME,https://www.$DOMAIN_NAME
REDIS_PASSWORD=$(openssl rand -base64 16)
GRAFANA_PASSWORD=$(openssl rand -base64 16)
REACT_APP_API_URL=https://$DOMAIN_NAME/api
EOF
    log_warning "Please review and update backend/.env.production with your configuration"
fi

# Build and start services
log_info "Building and starting Docker services..."
docker-compose pull
docker-compose build
docker-compose up -d

# Wait for services to be ready
log_info "Waiting for services to be ready..."
sleep 30

# Check service health
log_info "Checking service health..."
if docker-compose ps | grep -q "Up"; then
    log_success "Services are running"
else
    log_error "Some services failed to start. Check logs with: docker-compose logs"
    exit 1
fi

# Run database migrations
log_info "Running database migrations..."
docker-compose exec backend python -m alembic upgrade head
log_success "Database migrations completed"

# Setup log rotation
log_info "Setting up log rotation..."
cat > /etc/logrotate.d/docker-containers << EOF
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=100M
    missingok
    delaycompress
    copytruncate
}
EOF
log_success "Log rotation configured"

# Setup backup script
log_info "Setting up backup script..."
cat > /usr/local/bin/backup-flashcard.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/flashcard"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/opt/flashcard-learning"

mkdir -p $BACKUP_DIR

# Backup database
docker-compose -f $PROJECT_DIR/docker-compose.yml exec -T postgres pg_dump -U flashcard_user flashcard_production > $BACKUP_DIR/db_$DATE.sql

# Backup uploads
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz -C $PROJECT_DIR backend/uploads

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /usr/local/bin/backup-flashcard.sh

# Setup backup cron job
echo "0 2 * * * root /usr/local/bin/backup-flashcard.sh >> /var/log/backup.log 2>&1" > /etc/cron.d/flashcard-backup
log_success "Backup system configured"

# Final system status
echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo "=================================================="
log_info "Your Flashcard Learning System is now running at:"
log_info "🌐 Frontend: https://$DOMAIN_NAME"
log_info "📊 Monitoring: https://$DOMAIN_NAME/grafana"
log_info "📁 Project Directory: $PROJECT_DIR"
echo ""
log_info "Important next steps:"
echo "1. Review and update backend/.env.production with your specific configuration"
echo "2. Create an admin user through the API or admin interface"
echo "3. Configure monitoring alerts in Grafana"
echo "4. Test the backup system: /usr/local/bin/backup-flashcard.sh"
echo ""
log_info "Useful commands:"
echo "- View logs: cd $PROJECT_DIR && docker-compose logs"
echo "- Restart services: cd $PROJECT_DIR && docker-compose restart"
echo "- Update application: cd $PROJECT_DIR && git pull && docker-compose up -d --build"
echo ""
log_warning "Don't forget to:"
echo "- Change default passwords in .env.production"
echo "- Configure email settings for notifications"
echo "- Set up monitoring alerts"
echo "- Test SSL certificate renewal"
