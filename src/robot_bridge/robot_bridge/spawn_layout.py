"""Spawn (x, y) per slot index; keep in sync with amcl_seed_pose."""


def spawn_xy_for_slot(slot_index: int) -> tuple[float, float]:
    if slot_index < 0:
        raise ValueError("slot_index must be >= 0")
    # Third robot: offset from the (0,0)-(1.5,0) line so it is easier to see in Gazebo.
    if slot_index == 2:
        return (0.7, 1.0)
    return float((slot_index % 5) * 1.5), float((slot_index // 5) * 1.5)
