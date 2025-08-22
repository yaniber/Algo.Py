# MetaTrader5 Configuration

This directory contains configuration files for MetaTrader5 setup in the Docker environment.

## Setup

After running `docker-compose up`, execute the MT5 setup script:

```bash
docker exec -it algopy_app ./scripts/setup_mt5_wine.sh
```

## Configuration Files

- Place your broker-specific configuration files here
- Terminal configuration files will be generated during setup
- Login credentials should be configured through the MT5 setup script

## Service Management

Use supervisorctl to manage MT5 services:

```bash
# Check service status
docker exec -it algopy_app supervisorctl status

# Start MT5 terminal
docker exec -it algopy_app supervisorctl start mt5

# View logs
docker exec -it algopy_app supervisorctl tail -f mt5
```