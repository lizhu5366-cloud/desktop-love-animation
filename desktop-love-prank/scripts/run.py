"""Desktop love-prank: pop cat GIFs on screen in a heart shape, then flood the screen.

Usage:
    python run.py                          # default: 70 hearts, 350 flood, music on
    python run.py --message "嫁给我吧"      # custom window title / toast
    python run.py --heart-count 50 --fill-count 200
    python run.py --no-sound
    python run.py --gifs-dir C:/path/to/gifs --music C:/path/to/music.mp3

Close: press ESC, or double-click / right-click any window.
"""
from __future__ import annotations

import argparse
import math
import random
import sys
import time
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk

from sound_player import SoundPlayer
from animation_loader import (
    load_animation,
    trim_frames_to_content,
)

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GIFS = SKILL_ROOT / "assets" / "gifs"
DEFAULT_MUSIC = SKILL_ROOT / "assets" / "music.mp3"

MAX_SCREEN_FRACTION = 0.95


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Desktop love-prank animation")
    p.add_argument("--message", default="我真的特别爱你", help="Window title / affection text")
    p.add_argument("--gifs-dir", default=str(DEFAULT_GIFS), help="Directory containing .gif files")
    p.add_argument("--music", default=str(DEFAULT_MUSIC), help="MP3 file to play")
    p.add_argument("--no-sound", action="store_true", help="Disable background music")
    p.add_argument("--no-topmost", action="store_true", help="Don't keep windows on top")
    p.add_argument("--heart-count", type=int, default=70, help="Number of GIFs that form the heart")
    p.add_argument("--fill-count", type=int, default=350, help="Number of GIFs that flood the screen")
    p.add_argument("--heart-interval", type=int, default=35, help="Ms between each heart point spawn")
    p.add_argument("--heart-hold", type=int, default=3000, help="Ms to hold the heart before clearing")
    p.add_argument("--fill-interval", type=int, default=10, help="Ms between each flood spawn")
    p.add_argument("--scale", type=float, default=2.5, help="Scale factor for single-GIF mode")
    p.add_argument("--alpha-threshold", type=int, default=200)
    return p.parse_args()


def discover_gifs(gifs_dir: str) -> list[Path]:
    d = Path(gifs_dir)
    if d.is_file():
        return [d]
    gifs = sorted({c.resolve() for c in d.iterdir() if c.suffix.lower() == ".gif"})
    if not gifs:
        raise FileNotFoundError(f"No .gif files in: {d}")
    return gifs


def harden_alpha(image: Image.Image, cutoff: int) -> Image.Image:
    if cutoff <= 0:
        return image.convert("RGBA")
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A").point(lambda a: 255 if a >= cutoff else 0)
    rgba.putalpha(alpha)
    return rgba


def build_frames(frames, target_size, smooth, alpha_threshold):
    resample = Image.Resampling.LANCZOS if smooth else Image.Resampling.NEAREST
    background = Image.new("RGBA", target_size, (0, 0, 0, 255))
    photos, durations = [], []
    for frame in frames:
        resized = frame.image.convert("RGBA").resize(target_size, resample)
        hardened = harden_alpha(resized, alpha_threshold)
        composed = Image.alpha_composite(background, hardened).convert("RGB")
        photos.append(ImageTk.PhotoImage(composed))
        durations.append(max(10, int(round(frame.duration * 1000))))
    return photos, durations


class AnimationWindow:
    def __init__(self, root, photos, durations, size, position, topmost, on_close):
        self.root = root
        self.photos = photos
        self.durations = durations
        self.on_close = on_close
        self.destroyed = False
        self.top = tk.Toplevel(root)
        self.top.overrideredirect(True)
        border = 6
        self.top.geometry(f"{size[0]+border}x{size[1]+border}+{position[0]}+{position[1]}")
        if topmost:
            try:
                self.top.wm_attributes("-topmost", True)
            except tk.TclError:
                pass
        self.frame = tk.Frame(self.top, bg="#ff85a2", bd=3)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.label = tk.Label(self.frame, bd=0, highlightthickness=0, bg="black", image=self.photos[0])
        self.label.pack(fill=tk.BOTH, expand=True)
        self.top.bind("<Double-Button-1>", lambda e: self._request_close())
        self.top.bind("<Button-3>", lambda e: self._request_close())
        self.index = 0
        self.next_due = time.perf_counter() + self.durations[0] / 1000.0

    def tick(self, now):
        if self.destroyed:
            return
        if now >= self.next_due:
            self.index = (self.index + 1) % len(self.photos)
            try:
                self.label.configure(image=self.photos[self.index])
            except tk.TclError:
                return
            self.next_due = max(now, self.next_due) + self.durations[self.index] / 1000.0

    def _request_close(self):
        if self.on_close:
            self.on_close()

    def destroy(self):
        self.destroyed = True
        try:
            self.top.destroy()
        except tk.TclError:
            pass


def main() -> int:
    args = parse_args()
    try:
        gif_paths = discover_gifs(args.gifs_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    root = tk.Tk()
    root.withdraw()
    root.title(args.message)
    screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
    base_dim = min(screen_w, screen_h)

    # Pre-build frame pools for several sizes
    raw_frames = []
    for path in gif_paths:
        try:
            f = load_animation(path)
            f = trim_frames_to_content(f)
            if f:
                raw_frames.append(f)
        except Exception:
            pass
    if not raw_frames:
        print("Error: no usable GIF frames", file=sys.stderr)
        return 1

    sizes = [base_dim // 14, base_dim // 12, base_dim // 10, base_dim // 8, base_dim // 6]
    photo_pools = []
    for size in sizes:
        pool = []
        for frames in raw_frames:
            photos, durations = build_frames(frames, (size, size), False, args.alpha_threshold)
            pool.append((photos, durations))
        photo_pools.append(pool)

    # Audio
    audio_player = None
    if not args.no_sound:
        music_path = Path(args.music)
        if music_path.exists():
            try:
                audio_player = SoundPlayer(music_path)
                audio_player.start()
            except Exception:
                pass

    windows = []
    closing = {"flag": False}

    def close_all(event=None):
        if closing["flag"]:
            return
        closing["flag"] = True
        for w in windows:
            w.destroy()
        try:
            root.destroy()
        except tk.TclError:
            pass
        if audio_player:
            try:
                audio_player.stop()
            except Exception:
                pass

    root.bind_all("<Escape>", close_all)

    def global_tick():
        if closing["flag"]:
            return
        now = time.perf_counter()
        for w in windows:
            w.tick(now)
        root.after(15, global_tick)

    def phase_heart():
        if closing["flag"]:
            return
        num_heart = max(1, args.heart_count)
        scale = min(screen_w / 45.0, screen_h / 45.0) * 0.85
        size = sizes[0]

        def spawn(i):
            if closing["flag"]:
                return
            if i < num_heart:
                th = i / num_heart * 2 * math.pi
                x = 16 * math.sin(th) ** 3
                y = 13 * math.cos(th) - 5 * math.cos(2 * th) - 2 * math.cos(3 * th) - math.cos(4 * th)
                sx = int(screen_w / 2 + x * scale - size / 2)
                sy = int(screen_h / 2 - y * scale - size / 2)
                sx = max(0, min(sx, screen_w - size))
                sy = max(0, min(sy, screen_h - size))
                photos, durations = random.choice(photo_pools[0])
                windows.append(AnimationWindow(root, photos, durations, (size, size), (sx, sy), not args.no_topmost, close_all))
                root.after(max(1, args.heart_interval), spawn, i + 1)
            else:
                root.after(max(500, args.heart_hold), phase_clear)

        global_tick()
        spawn(0)

    def phase_clear():
        if closing["flag"]:
            return
        for w in windows:
            w.destroy()
        windows.clear()
        root.after(100, phase_fill)

    def phase_fill():
        if closing["flag"]:
            return
        total = max(1, args.fill_count)

        def spawn_next(index):
            if closing["flag"] or index >= total:
                return
            size_idx = random.choice([2, 3, 3, 4, 4])
            size = sizes[size_idx]
            sx = random.randint(0, max(0, screen_w - size))
            sy = random.randint(0, max(0, screen_h - size))
            photos, durations = random.choice(photo_pools[size_idx])
            windows.append(AnimationWindow(root, photos, durations, (size, size), (sx, sy), not args.no_topmost, close_all))
            root.after(max(1, args.fill_interval), spawn_next, index + 1)

        spawn_next(0)

    root.after(50, phase_heart)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        close_all()
    return 0


if __name__ == "__main__":
    sys.exit(main())
