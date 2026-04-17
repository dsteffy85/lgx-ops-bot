# LGX-OPS-BOT — SKI Deployment

## Overview

LGX-OPS-BOT is a Slack listener that polls channels for hardware-delivery and logistics questions, queries Snowflake/Databricks, and posts answers. It runs as a single-replica Kubernetes deployment on the SKI platform.

## Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌───────────────────┐
│  Slack API   │◄───►│  lgx-ops-bot pod │────►│  Snowflake        │
│  slack.com   │     │  (python 3.11)   │────►│  Databricks       │
└──────────────┘     └──────────────────┘     └───────────────────┘
                        :8080 /health
                        :8080 /ready
```

## Prerequisites

1. **Docker image** pushed to `docker.sqprod.co/sq-logistics/lgx-ops-bot`
2. **K8s secrets** created in the `sq-logistics` namespace:
   - `lgx-ops-bot-slack-token` — key: `token`
   - `lgx-ops-bot-snowflake-key` — key: `private_key.pem`
   - `lgx-ops-bot-databricks-token` — key: `token`

## Deploying

### Build & push the image

```bash
# CI builds automatically on merge to main via kochiku.yml
# Manual build:
docker build -t docker.sqprod.co/sq-logistics/lgx-ops-bot:latest .
docker push docker.sqprod.co/sq-logistics/lgx-ops-bot:latest
```

### Create secrets (one-time)

```bash
kubectl -n sq-logistics create secret generic lgx-ops-bot-slack-token \
    --from-literal=token="xoxb-..."

kubectl -n sq-logistics create secret generic lgx-ops-bot-snowflake-key \
    --from-file=private_key.pem=/path/to/rsa_key.p8

kubectl -n sq-logistics create secret generic lgx-ops-bot-databricks-token \
    --from-literal=token="dapi..."
```

### Apply SKI templates

```bash
kubectl apply -f ski/serviceaccount.yaml.template
kubectl apply -f ski/deployment.yaml.template
kubectl apply -f ski/pdb.yaml.template
```

### Verify

```bash
kubectl -n sq-logistics get pods -l app=lgx-ops-bot
kubectl -n sq-logistics logs -f deployment/lgx-ops-bot
curl http://<pod-ip>:8080/health
```

## Health Endpoints

| Path      | Success | Failure | Description                        |
|-----------|---------|---------|------------------------------------|
| `/health` | 200     | —       | Process is alive, returns uptime   |
| `/ready`  | 200     | 503     | Listener poll loop is active       |

## Outbound Network Requirements

The pod requires egress to:
- `slack.com` / `api.slack.com` (Slack API)
- `square.snowflakecomputing.com` (Snowflake)
- `block-lakehouse-production.cloud.databricks.com` (Databricks)

## Troubleshooting

- **Pod CrashLoopBackOff**: Check logs for missing secrets or bad credentials.
- **Readiness probe failing**: The listener hasn't started its poll loop yet — check for Slack token issues.
- **OOMKilled**: Increase memory limit in `deployment.yaml.template` (default 256Mi).
