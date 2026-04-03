# Contributing

## Issues

[Open an issue](https://github.com/SamsonAjadalu/metal-to-cloud-telemetry/issues) for bugs or questions. Say what you expected, what happened, and how to reproduce.

## Branches

- Work in **`telemetry`**, **`frontend`**, **`backend`**, etc.
- **`prod`** = stable cloud deployment.
- **`main`** = stable snapshot (updated when a feature is done).

## Pull requests

Target a **dev** branch above, not `main`/`prod` for WIP. Small, focused PRs; describe what changed and why.

If you changed `src/robot_bridge`:

```bash
source /opt/ros/humble/setup.bash
cd /path/to/metal-to-cloud-telemetry
colcon build --packages-select robot_bridge --symlink-install
colcon test --packages-select robot_bridge && colcon test-result --verbose
```

No secrets in git — use `.env.telemetry` locally. Don’t change WebSocket/JSON shapes in `TELEMETRY_README.md` without team agreement.

Contributions are under the **MIT License** (`LICENSE`).
