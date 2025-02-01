# CFDI Invoicing System Deployment Guide

This guide explains how to deploy the CFDI Invoicing System to different environments.

## Prerequisites

- Docker and Docker Compose installed on the target machine
- Access to SW Sapien API credentials
- PostgreSQL database (provided via Docker)

## Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your_secure_se
cret_key

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/pos_db

# SW Sapien API Configuration
SW_URL=https://services.sw.com.mx
SW_TOKEN=your_sw_sapien_token

# SAT Configuration
SAT_RFC=your_rfc
SAT_NOMBRE=your_business_name
SAT_REGIMEN_FISCAL=601
SAT_CP=your_postal_code
```

## Deployment Steps

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd windsurf-project
   ```

2. Create and configure the `.env` file as shown above.

3. Build and start the containers:
   ```bash
   docker-compose up -d --build
   ```

4. Initialize the database:
   ```bash
   docker-compose exec web python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

5. Access the application at `http://your-server:8000`

## Health Check

Verify the deployment:
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f web
```

## Backup and Restore

1. Backup the database:
   ```bash
   docker-compose exec db pg_dump -U postgres pos_db > backup.sql
   ```

2. Restore the database:
   ```bash
   cat backup.sql | docker-compose exec -T db psql -U postgres -d pos_db
   ```

## Scaling

To scale the web service:
```bash
docker-compose up -d --scale web=3
```

## Monitoring

Monitor the application using Docker's built-in tools:
```bash
# View container stats
docker stats

# View container logs
docker-compose logs -f
```

## Troubleshooting

1. If the web service fails to start:
   - Check the logs: `docker-compose logs web`
   - Verify environment variables
   - Ensure database connection is working

2. If database connection fails:
   - Verify PostgreSQL is running: `docker-compose ps db`
   - Check database credentials in `.env`
   - Ensure database initialization was successful

3. If SW Sapien API calls fail:
   - Verify API credentials in `.env`
   - Check network connectivity to SW Sapien servers
   - Review API response in logs

## Security Notes

1. Always use strong passwords and secret keys
2. Keep the `.env` file secure and never commit it to version control
3. Regularly update dependencies and Docker images
4. Use HTTPS in production
5. Implement rate limiting if needed

## Maintenance

1. Update dependencies:
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

2. Database migrations:
   ```bash
   docker-compose exec web flask db upgrade
   ```

3. Cleanup:
   ```bash
   docker-compose down -v  # Remove containers and volumes
   docker system prune     # Clean up unused resources
   ```
