# FlashLearn Production Deployment Guide

## 🚀 Production Ready Setup

Your FlashLearn application has been successfully configured for production deployment with the following optimizations:

### ✅ Security & Performance Features
- **Single Port Exposure**: Only port 3000 is exposed to the outside world
- **Internal Network**: Backend and database communicate through secure internal Docker network
- **Nginx Reverse Proxy**: Production-grade web server with caching and compression
- **Optimized Images**: Multi-stage Docker builds for minimal image sizes
- **Health Checks**: Automatic container health monitoring

### 📦 What's Included

1. **Production Docker Compose**: `docker-compose.production.yml`
2. **Optimized Frontend**: Production build with Nginx (53.3MB)
3. **Backend API**: FastAPI with production settings (728MB)
4. **PostgreSQL Database**: Persistent data storage
5. **Custom Nginx Config**: Proper routing and security headers

## 🔧 Deployment Instructions

### Quick Start
```bash
# Clone/copy your application files to the server
# Navigate to the application directory
cd /path/to/flash_cards

# Start the production environment
docker-compose -f docker-compose.production.yml up -d

# Verify all services are running
docker-compose -f docker-compose.production.yml ps
```

### System Requirements
- **Docker Engine**: 20.10+
- **Docker Compose**: 2.0+
- **RAM**: Minimum 2GB, Recommended 4GB
- **Storage**: 2GB for images + data storage
- **Ports**: Port 3000 must be available

### Environment Variables
The production setup uses these key configurations:
- `VITE_API_BASE_URL=/api/v1` - API routing through nginx
- `ENVIRONMENT=production` - Backend production mode
- `DATABASE_URL=postgresql://...` - Internal database connection
- `ALLOWED_ORIGINS=http://localhost:3000` - CORS configuration

## 🌐 Server Deployment

### For Cloud Deployment (AWS, GCP, Azure, etc.)

1. **Prepare the server**:
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Upload application files**:
   - Copy the entire project directory to your server
   - Ensure `docker-compose.production.yml` is present

3. **Configure firewall**:
   ```bash
   # Allow port 3000
   sudo ufw allow 3000/tcp
   ```

4. **Start the application**:
   ```bash
   docker-compose -f docker-compose.production.yml up -d
   ```

### For Domain Setup

1. **Update CORS settings** in `docker-compose.production.yml`:
   ```yaml
   environment:
     - ALLOWED_ORIGINS=https://yourdomain.com,http://yourdomain.com
   ```

2. **Add reverse proxy** (recommended with SSL):
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       location / {
           proxy_pass http://localhost:3000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## 🔍 Verification & Testing

### Health Checks
```bash
# Check container status
docker-compose -f docker-compose.production.yml ps

# Check application logs
docker-compose -f docker-compose.production.yml logs

# Test the application
curl http://localhost:3000
curl http://localhost:3000/api/v1/admin/config/learning/public
```

### Expected Responses
- **Frontend**: HTML page with the FlashLearn application
- **API**: JSON response with learning configuration
- **All containers**: Should show "healthy" status

## 🛠 Maintenance Commands

```bash
# View logs
docker-compose -f docker-compose.production.yml logs -f

# Restart services
docker-compose -f docker-compose.production.yml restart

# Update the application
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml up -d

# Backup database
docker-compose -f docker-compose.production.yml exec postgres pg_dump -U flashcard_user flashcard_db > backup.sql

# Stop all services
docker-compose -f docker-compose.production.yml down
```

## 🔒 Security Considerations

1. **Change default passwords** in production
2. **Use environment files** for sensitive data
3. **Enable SSL/HTTPS** with Let's Encrypt or similar
4. **Regular backups** of database and user data
5. **Monitor logs** for security issues

## 📊 Architecture Overview

```
Internet -> Port 3000 -> Nginx (Frontend) -> Internal Network
                            ↓
                         Backend API (Port 8000) -> PostgreSQL (Port 5432)
```

- **Frontend**: React app served by Nginx on port 80 (mapped to 3000)
- **Backend**: FastAPI server on internal port 8000
- **Database**: PostgreSQL on internal port 5432
- **Networking**: All internal communication through Docker network

## 🚨 Troubleshooting

### Common Issues

1. **Port 3000 already in use**:
   ```bash
   sudo lsof -i :3000
   # Kill the process or change the port mapping
   ```

2. **Database connection errors**:
   ```bash
   # Check if PostgreSQL is healthy
   docker-compose -f docker-compose.production.yml exec postgres pg_isready -U flashcard_user
   ```

3. **API 404 errors**:
   - Verify nginx configuration is correct
   - Check that backend container is running
   - Ensure API paths include `/v1/` prefix

4. **Build failures**:
   ```bash
   # Clean rebuild
   docker-compose -f docker-compose.production.yml build --no-cache
   ```

## ✅ Success Indicators

Your deployment is successful when:
- ✅ All 3 containers are running and healthy
- ✅ Frontend loads at `http://localhost:3000`
- ✅ API responds at `http://localhost:3000/api/v1/admin/config/learning/public`
- ✅ Login attempts return 401 (not 404 or 500)
- ✅ Dynamic rules show up on the homepage with actual values

---

## 🎉 Congratulations!

Your FlashLearn application is now production-ready with:
- **Optimized Performance**: Nginx caching and compression
- **Security**: Internal networking and minimal attack surface  
- **Scalability**: Docker-based architecture ready for orchestration
- **Maintainability**: Health checks and logging included

Access your application at: **http://localhost:3000**

For production deployment, replace `localhost` with your domain name and ensure proper SSL configuration.
