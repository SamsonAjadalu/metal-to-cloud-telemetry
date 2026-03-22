# DigitalOcean Persistent Storage Setup

This guide shows how to attach a DigitalOcean Block Storage Volume so that
PostgreSQL data **survives even if the entire droplet is destroyed and recreated**.

---

## Step 1 — Create a Block Storage Volume

```bash
# Via CLI (install doctl first: brew install doctl)
doctl compute volume create pg-data-volume \
  --region nyc1 \
  --size 10GiB \
  --desc "PostgreSQL persistent storage for Metal-to-Cloud"
```

Or via the DigitalOcean Console:  
**Volumes → Create Volume → 10 GB → Same region as your droplet → Attach to your droplet**

---

## Step 2 — Mount the Volume on the Droplet

SSH into the droplet and run:

```bash
# Find the volume device (usually /dev/disk/by-id/scsi-0DO_Volume_pg-data-volume)
ls /dev/disk/by-id/

# Format it (ONLY do this the very first time, this erases all data!)
sudo mkfs.ext4 /dev/disk/by-id/scsi-0DO_Volume_pg-data-volume

# Create mount point
sudo mkdir -p /mnt/pg_data

# Mount it
sudo mount /dev/disk/by-id/scsi-0DO_Volume_pg-data-volume /mnt/pg_data

# Make it persistent across reboots
echo "/dev/disk/by-id/scsi-0DO_Volume_pg-data-volume /mnt/pg_data ext4 defaults,nofail,discard 0 2" | sudo tee -a /etc/fstab

# Set permissions for Docker
sudo chmod 777 /mnt/pg_data
```

---

## Step 3 — Update compose.yaml

Change the volumes section at the bottom of `compose.yaml`:

```yaml
volumes:
  pg_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/pg_data
```

This tells Docker to store PostgreSQL data on the DigitalOcean Volume
instead of Docker's default storage location.

---

## Step 4 — Redeploy

```bash
# If using Docker Swarm:
docker stack deploy -c compose.yaml m2c

# If using Docker Compose:
docker compose down
docker compose up -d
```

---

## Step 5 — Verify Persistence

1. Connect a fake robot and let it send telemetry for ~30 seconds
2. Check the fleet table on the dashboard — you should see the robot with distance traveled
3. Stop and remove all containers:
   ```bash
   docker compose down
   ```
4. Start them again:
   ```bash
   docker compose up -d
   ```
5. Check the dashboard again — the fleet table should still show the robot's **total distance**, **last known position**, and **last seen** timestamp from before the restart

This proves PostgreSQL data is stored on the DigitalOcean Volume and
survives container lifecycle events.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────┐
│  DigitalOcean Droplet                            │
│                                                  │
│  ┌─────────┐  ┌─────────┐  ┌──────────────────┐ │
│  │Frontend │  │  API    │  │   PostgreSQL     │ │
│  │ (Nginx) │  │(FastAPI)│  │  ┌────────────┐  │ │
│  │ :3000   │  │ :8000   │──│  │ telemetries│  │ │
│  └─────────┘  └─────────┘  │  │ robots     │  │ │
│                            │  └────────────┘  │ │
│                            │     ↕ mounted    │ │
│                            └──────────────────┘ │
│                                   ↕             │
│                    ┌──────────────────────────┐  │
│                    │  /mnt/pg_data            │  │
│                    │  (DigitalOcean Volume)   │  │
│                    │  Survives droplet destroy│  │
│                    └──────────────────────────┘  │
└──────────────────────────────────────────────────┘
```
