"""Fleet spawn (x, y) per slot; shared with amcl_seed_pose so map pose matches Gazebo."""


def spawn_xy_for_slot(slot_index: int) -> tuple[float, float]:
    if slot_index < 0:
        raise ValueError("slot_index must be >= 0")
    # Slots 0–1: unchanged at (0,0) and (1.5,0). Slot 2: between them in x, small +y (~1 m)
    # so it stays near the pair and visible (was (3,0) then (1.5,2.5) — still hard to see).
    if slot_index == 2:
        return (0.7, 1.0)
    return float((slot_index % 5) * 1.5), float((slot_index // 5) * 1.5)
