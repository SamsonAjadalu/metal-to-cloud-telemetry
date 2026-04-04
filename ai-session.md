# AI Interaction Record

This file supports the **AI Assistance & Verification** section of the final report. It documents representative interactions where AI tools influenced the project, including cases where output was corrected or rejected after verification.

---

## Session 1: Configuring CORS for Production

### Prompt (you sent to AI)

How do I fix the "Blocked by CORS policy" error when my React frontend talks to my FastAPI backend in Docker?

### AI Response (trimmed if long)

You can fix this quickly by adding the `CORSMiddleware` to your FastAPI app. To make sure it accepts requests from anywhere, you can set `allow_origins=["*"]` and set `allow_credentials=True`.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### What Your Team Did With It

- **What was useful:** It correctly identified that we needed to import and attach `CORSMiddleware` to our FastAPI instance.
- **What was incorrect, misleading, or not applicable:** The suggestion to use a wildcard (`"*"`) alongside `allow_credentials=True` is a poor fit for a cloud-facing deployment. Browsers also restrict credential flows with a wildcard origin, so the snippet as given would not behave reliably in production.
- **How your team verified, modified, or replaced the suggestion:** We used browser network logs to confirm the failure mode, rejected the wildcard approach, and implemented a strict allowlist via **`CORS_ALLOW_ORIGINS`**. We validated locally and against production so only our dashboard origin (e.g. `http://159.203.4.11:3000`) could call the API.

---

## Session 2: Orchestrating High Availability in Docker Swarm

### Prompt (you sent to AI)

How do I configure my `compose.yaml` to make sure my frontend has high availability and runs on multiple nodes in Docker Swarm?

### AI Response (trimmed if long)

You need to use the `deploy` key in your compose configuration. Under your frontend service, you can specify the replication mode and the number of replicas you want.

```yaml
services:
  frontend:
    image: wofa/m2c-frontend:latest
    deploy:
      mode: replicated
      replicas: 2
```

### What Your Team Did With It

- **What was useful:** It gave the correct Swarm-style YAML pattern (`deploy`, `replicas`) that differs from plain local Compose.
- **What was incorrect, misleading, or not applicable:** The answer stayed minimal and did not call out placement constraints, resource limits, or restart behavior, which mattered for our manager/worker layout on DigitalOcean.
- **How your team verified, modified, or replaced the suggestion:** We merged the `deploy` / replica idea into our real `compose.yaml`, then added restart and placement rules appropriate to our stack. We verified with **`docker service ls`** on the manager (e.g. frontend at **2/2**) and used Grafana / traffic checks to confirm load was spread across nodes.
