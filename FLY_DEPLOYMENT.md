# Deploying to fly.io

This guide explains how to deploy the CFDI Invoicing System to fly.io.

## Prerequisites

1. Install flyctl:
```bash
curl -L https://fly.io/install.sh | sh
```

2. Login to fly.io:
```bash
flyctl auth login
```

## Configuration

1. Set up your secrets:
```bash
# Database URL will be automatically set by fly.io
flyctl secrets set SW_URL=https://services.sw.com.mx
flyctl secrets set SW_TOKEN=your_sw_token
flyctl secrets set SAT_RFC=your_rfc
flyctl secrets set SAT_NOMBRE=your_business_name
flyctl secrets set SAT_REGIMEN_FISCAL=601
flyctl secrets set SAT_CP=your_postal_code
flyctl secrets set SECRET_KEY=your_secure_key
```

## Database Setup

1. Create a PostgreSQL database:
```bash
flyctl postgres create cfdi-pos-db
```

2. Attach the database to your app:
```bash
flyctl postgres attach cfdi-pos-db
```

## Deployment

1. Launch the app:
```bash
flyctl launch
```

2. Deploy updates:
```bash
flyctl deploy
```

## Monitoring

1. View app status:
```bash
flyctl status
```

2. Check logs:
```bash
flyctl logs
```

3. Monitor metrics:
```bash
flyctl metrics
```

## Scaling

1. Scale the app:
```bash
flyctl scale count 2  # Run 2 instances
```

2. Scale memory/CPU:
```bash
flyctl scale memory 512  # Set memory to 512MB
```

## Database Management

1. Connect to database:
```bash
flyctl postgres connect -a cfdi-pos-db
```

2. Backup database:
```bash
flyctl postgres backup -a cfdi-pos-db
```

## SSL/TLS

fly.io automatically handles SSL certificates and HTTPS. Your app will be available at:
https://cfdi-pos-system.fly.dev

## Troubleshooting

1. Check app health:
```bash
curl https://cfdi-pos-system.fly.dev/health
```

2. View deployment issues:
```bash
flyctl status
flyctl logs
```

3. Common issues:
- Database connection: Check DATABASE_URL in secrets
- Memory issues: Increase memory allocation
- CPU issues: Scale to more instances

## Maintenance

1. Update secrets:
```bash
flyctl secrets set KEY=VALUE
```

2. Restart app:
```bash
flyctl restart
```

3. SSH into instance:
```bash
flyctl ssh console
```
