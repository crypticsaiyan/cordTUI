# Container Naming Guide for DevOps Health Bot

## How Filtering Works

The DevOps Health Bot filters containers based on keywords in their names.

### Environment Keywords

The bot recognizes these environment keywords:
- `prod` or `production` → Production environment
- `staging` or `stage` → Staging environment  
- `dev` or `development` → Development environment

### Service Keywords

The bot recognizes these service keywords:
- `web` → Web servers
- `api` → API services
- `db` or `database` → Databases
- `worker` → Background workers
- `redis` → Redis instances
- `nginx` → Nginx servers
- `payments` → Payment services

## Examples

### Query: `/ai prod-web`

**Matches containers with BOTH "prod" AND "web" in the name:**
- ✅ `prod-web-1`
- ✅ `prod-web-api`
- ✅ `my-prod-web-server`
- ❌ `prod-api` (no "web")
- ❌ `staging-web` (no "prod")
- ❌ `goofy_keldysh` (neither "prod" nor "web")

### Query: `/ai prod`

**Matches containers with "prod" in the name:**
- ✅ `prod-web-1`
- ✅ `prod-api`
- ✅ `production-db`
- ❌ `staging-web`
- ❌ `goofy_keldysh`

### Query: `/ai web`

**Matches containers with "web" in the name:**
- ✅ `prod-web-1`
- ✅ `staging-web`
- ✅ `my-web-server`
- ❌ `prod-api`
- ❌ `goofy_keldysh`

### Query: `/ai` (no filter)

**Matches ALL containers:**
- ✅ `prod-web-1`
- ✅ `staging-api`
- ✅ `goofy_keldysh`
- ✅ Everything!

## Recommended Naming Convention

For best results with the health bot, name your containers using this pattern:

```
{environment}-{service}-{instance}
```

### Examples:

**Production:**
- `prod-web-1`, `prod-web-2`
- `prod-api-1`, `prod-api-2`
- `prod-db-primary`, `prod-db-replica`
- `prod-worker-1`
- `prod-redis-1`

**Staging:**
- `staging-web-1`
- `staging-api-1`
- `staging-db-1`

**Development:**
- `dev-web-1`
- `dev-api-1`

## Docker Compose Example

```yaml
version: '3.8'
services:
  web:
    image: nginx
    container_name: prod-web-1
    
  api:
    image: myapp/api
    container_name: prod-api-1
    
  db:
    image: postgres
    container_name: prod-db-primary
    
  worker:
    image: myapp/worker
    container_name: prod-worker-1
```

## Using Docker Labels (Alternative)

You can also use Docker labels for filtering:

```bash
docker run -d \
  --name my-container \
  --label environment=prod \
  --label service=web \
  nginx
```

The bot will check labels if the name doesn't match.

## Your Current Containers

Based on your Docker output, you have:
- `goofy_keldysh` - Random Docker name (no environment/service info)
- `quizzical_nobel` - Random Docker name
- `fervent_jackson` - Random Docker name
- `dreamy_khorana` - Random Docker name
- `kind_neumann` - Random Docker name

**These won't match filters like `/ai prod-web` because they don't contain those keywords.**

### To Fix:

Rename your containers using the naming convention:

```bash
# Stop and remove old container
docker stop goofy_keldysh
docker rm goofy_keldysh

# Start with a proper name
docker run -d --name prod-web-1 nginx
```

Or use `docker rename`:

```bash
docker rename goofy_keldysh prod-web-1
```

## Testing

```bash
# Create test containers
docker run -d --name prod-web-1 nginx
docker run -d --name prod-api-1 nginx
docker run -d --name staging-web-1 nginx

# Test filtering
python3 -c "
import asyncio
from src.core.devops_health_bot import DevOpsHealthBot

async def test():
    bot = DevOpsHealthBot()
    
    print('All containers:')
    print(await bot.check_health(''))
    print()
    
    print('Production only:')
    print(await bot.check_health('prod'))
    print()
    
    print('Web services only:')
    print(await bot.check_health('web'))
    print()
    
    print('Production web:')
    print(await bot.check_health('prod-web'))

asyncio.run(test())
"

# Cleanup
docker stop prod-web-1 prod-api-1 staging-web-1
docker rm prod-web-1 prod-api-1 staging-web-1
```

## Summary

✅ **Fixed:** Container names now display correctly (not "unknown")
✅ **Working:** Filtering by environment and service keywords
✅ **Recommendation:** Use descriptive container names with environment and service info

The bot is working correctly! If you want to use filters like `/ai prod-web`, make sure your containers have those keywords in their names.
