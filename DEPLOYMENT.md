# Flashcard Learning System - Deployment Guide
# ============================================

## Overview

This document provides comprehensive instructions for deploying the Flashcard Learning System in various environments, from local development to production deployment.

## 🏗️ Architecture Overview

The system consists of:
- **Backend**: FastAPI application with PostgreSQL database
- **Frontend**: React application 
- **Database**: PostgreSQL for data persistence
- **Cache**: Redis for session management and caching
- **Reverse Proxy**: Nginx for load balancing and SSL termination
- **Monitoring**: Prometheus + Grafana for observability

## 🚀 Quick Start - Local Development

### Prerequisites
- Docker and Docker Compose installed
- Git installed
- At least 4GB RAM available

### 1. Clone and Setup
```bash
git clone <your-repository-url>
cd flashcard-learning-system
```

### 2. Run Development Environment
```bash
./deploy-dev.sh
```

This script will:
- Create development environment configuration
- Build and start all services
- Run database migrations
- Optionally create test data

### 3. Access Services
- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Grafana Dashboard**: http://localhost:3001 (admin/admin)

## 🏭 Production Deployment

### Server Requirements
- Ubuntu 20.04+ (recommended)
- 2+ CPU cores
- 4GB+ RAM
- 20GB+ storage
- Domain name with DNS configured

### 1. Server Preparation

Update your domain DNS records:
```
A    yourdomain.com       -> YOUR_SERVER_IP
A    www.yourdomain.com   -> YOUR_SERVER_IP
```

### 2. Run Production Deployment
```bash
# On your server, as root or with sudo
wget https://raw.githubusercontent.com/your-repo/deploy.sh
chmod +x deploy.sh
sudo ./deploy.sh yourdomain.com admin@yourdomain.com
```

### 3. Post-Deployment Configuration

1. **Update Environment Variables**:
   ```bash
   cd /opt/flashcard-learning
   sudo nano backend/.env.production
   ```
   Update the following:
   - Database passwords
   - JWT secret key
   - Email configuration
   - Domain names

2. **Restart Services**:
   ```bash
   sudo docker-compose restart
   ```

3. **Create Admin User**:
   ```bash
   sudo docker-compose exec backend python -c "
   from app.auth.utils import create_admin_user
   create_admin_user('admin', 'admin@yourdomain.com', 'your-secure-password')
   "
   ```

## 🔧 Manual Deployment Steps

If you prefer manual setup or need customization:

### 1. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Configure Firewall
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

### 3. SSL Certificate
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

### 4. Application Deployment
```bash
# Create project directory
sudo mkdir -p /opt/flashcard-learning
cd /opt/flashcard-learning

# Copy your project files here
# Then start services
sudo docker-compose up -d
```

## 🔒 Security Configuration

### 1. Environment Variables
Ensure all sensitive data is properly configured:

```bash
# Generate secure passwords
openssl rand -base64 32  # For JWT_SECRET_KEY
openssl rand -base64 16  # For database passwords
```

### 2. Firewall Rules
```bash
# Only allow necessary ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### 3. SSL/TLS Configuration
The nginx configuration includes:
- TLS 1.2 and 1.3 only
- Strong cipher suites
- HSTS headers
- Secure SSL parameters

### 4. Rate Limiting
Configured in nginx.conf:
- API endpoints: 10 requests/second
- Authentication: 5 requests/minute
- Global rate limiting per IP

## 📊 Monitoring and Maintenance

### 1. Health Checks
```bash
# Check all services
sudo docker-compose ps

# View logs
sudo docker-compose logs -f

# Check specific service
sudo docker-compose logs backend
```

### 2. Backup System
Automated backups are configured to run daily:
```bash
# Manual backup
sudo /usr/local/bin/backup-flashcard.sh

# Restore from backup
sudo docker-compose exec postgres psql -U flashcard_user -d flashcard_production < backup.sql
```

### 3. Monitoring Dashboards
- **Grafana**: https://yourdomain.com/grafana
- **Prometheus**: Internal metrics collection
- **Application Logs**: Available via Docker Compose

### 4. Updates and Maintenance
```bash
# Update application
cd /opt/flashcard-learning
git pull origin main
sudo docker-compose pull
sudo docker-compose up -d --build

# Database migrations
sudo docker-compose exec backend python -m alembic upgrade head
```

## 🔍 Troubleshooting

### Common Issues

1. **Services won't start**:
   ```bash
   sudo docker-compose logs
   sudo docker-compose down
   sudo docker-compose up -d
   ```

2. **Database connection errors**:
   - Check DATABASE_URL in .env.production
   - Verify PostgreSQL is running: `sudo docker-compose ps postgres`

3. **SSL certificate issues**:
   ```bash
   sudo certbot renew --dry-run
   sudo nginx -t
   ```

4. **Frontend not loading**:
   - Check CORS_ORIGINS in backend configuration
   - Verify nginx configuration
   - Check React app build: `sudo docker-compose logs frontend`

### Log Locations
- Application logs: `sudo docker-compose logs [service]`
- Nginx logs: `/var/log/nginx/`
- System logs: `/var/log/syslog`

### Performance Issues
1. **High memory usage**:
   ```bash
   # Check container resources
   sudo docker stats
   
   # Adjust worker processes in docker-compose.yml
   ```

2. **Slow database queries**:
   ```bash
   # Access database for analysis
   sudo docker-compose exec postgres psql -U flashcard_user flashcard_production
   ```

## 🔄 CI/CD Pipeline

### GitHub Actions Setup
1. Fork the repository
2. Configure secrets in GitHub:
   - `GITHUB_TOKEN` (automatically provided)
   - Add production server details for deployment

### Automated Testing
The pipeline includes:
- Unit tests with pytest
- Frontend tests with Jest
- Security scanning with Trivy
- Code coverage reporting

### Deployment Workflow
- **Develop branch**: Deploys to staging
- **Main branch**: Deploys to production
- **Pull requests**: Run tests only

## 📞 Support

### Getting Help
1. Check the logs first: `sudo docker-compose logs`
2. Review this documentation
3. Check GitHub Issues for known problems
4. Create a new issue with:
   - Error messages
   - Steps to reproduce
   - System information

### Maintenance Schedule
- **Daily**: Automated backups
- **Weekly**: Check for security updates
- **Monthly**: Review monitoring metrics
- **Quarterly**: Update dependencies

---

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Domain name configured and pointing to server
- [ ] Server meets minimum requirements
- [ ] Backup strategy planned
- [ ] Monitoring alerts configured

### Deployment
- [ ] Run deployment script
- [ ] Update environment variables
- [ ] Generate SSL certificates
- [ ] Create admin user
- [ ] Test all functionality

### Post-Deployment
- [ ] Configure monitoring alerts
- [ ] Set up backup verification
- [ ] Document any custom configurations
- [ ] Train team on maintenance procedures

**🎉 Your Flashcard Learning System is now ready for production use!**
