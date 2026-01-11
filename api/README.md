# API Reference

This directory contains the OpenAPI specification for Agno Agent Starter.

## Interactive Documentation

When the server is running, access the interactive API docs at:

- **Swagger UI**: http://localhost:7777/docs
- **ReDoc**: http://localhost:7777/redoc

## OpenAPI Specification

The [`openapi.json`](./openapi.json) file contains the complete API specification in OpenAPI 3.1 format.

### For AI Tools

```python
# Read the spec programmatically
import json
with open("api/openapi.json") as f:
    spec = json.load(f)
```

### Core Endpoints

| Resource  | Endpoint                             | Description    |
| --------- | ------------------------------------ | -------------- |
| Agents    | `POST /agents/{agent_id}/runs`       | Run an agent   |
| Teams     | `POST /teams/{team_id}/runs`         | Run a team     |
| Workflows | `POST /workflows/{workflow_id}/runs` | Run a workflow |
| Sessions  | `GET /sessions`                      | List sessions  |
| Health    | `GET /health`                        | Health check   |

### Export the Latest Spec

```bash
python scripts/export_openapi.py
```

## Related

- [Agno Docs](https://docs.agno.com)
- [AgentOS Overview](https://docs.agno.com/agent-os/overview)
