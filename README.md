# bolt-client

A Python client library for interacting with Bolt Fleet Integration API and Supabase.

## Features

- **Bolt API Integration**: Complete client for Bolt Fleet Integration API with automatic token management
- **Supabase Client**: Pre-configured Supabase client for database operations
- **Type Safety**: Pydantic schemas for type-safe data handling
- **Automatic Token Refresh**: Handles OAuth token refresh automatically

## Installation

### From GitHub

#### Using HTTPS (Recommended)
```bash
pip install git+https://github.com/Taxibeee/bolt_client.git
```

#### Using SSH
```bash
pip install git+ssh://git@github.com/Taxibeee/bolt_client.git
```

#### For Development (Editable Install)
```bash
pip install -e git+https://github.com/Taxibeee/bolt_client.git#egg=bolt-client
```

## Usage

### Bolt Client

```python
from clients.bolt_client import bolt
from schemas.bolt_schemas import PortalStatus

# Get fleet orders
orders = bolt.get_fleet_orders(
    offset=0,
    limit=100,
    company_ids=[12345],
    start_ts=1699123456,
    end_ts=1699209856
)

# Get vehicles
vehicles = bolt.get_vehicles(
    offset=0,
    limit=100,
    company_id=12345,
    portal_status=PortalStatus.active
)

# Get drivers
drivers = bolt.get_drivers(
    offset=0,
    limit=100,
    company_id=12345,
    portal_status=PortalStatus.active
)

# Get fleet state logs
logs = bolt.get_fleet_state_logs(
    offset=0,
    limit=100,
    company_id=12345
)
```

### Supabase Client

```python
from clients.supabase_client import supabase

# Example query
response = supabase.table('your_table').select('*').execute()
```

## Configuration

Set the following environment variables:

```bash
# Bolt API Configuration
BOLT_CLIENT_ID=your_client_id
BOLT_CLIENT_SECRET=your_client_secret
BOLT_API_URL=https://api.bolt.eu

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## Requirements

- Python >= 3.12
- requests >= 2.31.0
- supabase >= 2.0.0
- python-dotenv >= 1.0.0
- pydantic >= 2.0.0

## License

MIT

