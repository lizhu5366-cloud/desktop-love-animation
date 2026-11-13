from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageSequence


@dataclass(frozen=True)
class AnimationFrame:
    image: Image.Image
    duration: float


def load_animation(file_path: str | Path) -> list[AnimationFrame]:
    anim_path = Path(file_path)
    frames: list[AnimationFrame] = []

    with Image.open(anim_path) as img:
        for frame in ImageSequence.Iterator(img):
            duration_ms = frame.info.get("duration", img.info.get("duration", 100))
            frame_duration = max(float(duration_ms) / 1000.0, 0.02)
            frames.append(AnimationFrame(frame.convert("RGBA").copy(), frame_duration))

    if not frames:
        raise ValueError(f"No frames found in animation: {anim_path}")

    return frames


def trim_frames_to_content(frames: Iterable[AnimationFrame]) -> list[AnimationFrame]:
    frame_list = list(frames)
    bounding_boxes = [frame.image.getchannel("A").getbbox() for frame in frame_list]
    bounding_boxes = [box for box in bounding_boxes if box is not None]

    if not frame_list or not bounding_boxes:
        return frame_list

    left_edge = min(box[0] for box in bounding_boxes)
    top_edge = min(box[1] for box in bounding_boxes)
    right_edge = max(box[2] for box in bounding_boxes)
    bottom_edge = max(box[3] for box in bounding_boxes)
    src_width, src_height = frame_list[0].image.size

    if (left_edge, top_edge, right_edge, bottom_edge) == (0, 0, src_width, src_height):
        return frame_list

    return [
        AnimationFrame(frame.image.crop((left_edge, top_edge, right_edge, bottom_edge)), frame.duration)
        for frame in frame_list
    ]
