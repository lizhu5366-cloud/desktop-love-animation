from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path


class SoundPlayer:
    def __init__(self, sound_path: str | Path) -> None:
        self.sound_path = Path(sound_path)
        self.playback_process: subprocess.Popen[bytes] | None = None

    def start(self) -> bool:
        if not self.sound_path.exists():
            return False

        cmd = self._get_play_command()
        if cmd is None:
            return False

        creation_flags = 0
        if os.name == "nt":
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP

        self.playback_process = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
        return True

    def stop(self) -> None:
        if self.playback_process is None or self.playback_process.poll() is not None:
            return

        self.playback_process.terminate()
        try:
            self.playback_process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            self.playback_process.kill()

    def _get_play_command(self) -> list[str] | None:
        os_type = platform.system()
        full_path = str(self.sound_path.resolve())

        if os_type == "Darwin" and shutil.which("afplay"):
            return ["afplay", full_path]

        if os_type == "Windows":
            shell_exe = shutil.which("powershell") or shutil.which("pwsh")
            if shell_exe:
                escaped_full_path = full_path.replace("'", "''")
                ps_script = (
                    "Add-Type -AssemblyName PresentationCore; "
                    f"$path = '{escaped_full_path}'; "
                    "$player = New-Object System.Windows.Media.MediaPlayer; "
                    "$player.Open((New-Object System.Uri($path))); "
                    "$player.Play(); "
                    "while (-not $player.NaturalDuration.HasTimeSpan) { "
                    "Start-Sleep -Milliseconds 50 "
                    "}"
                    "Start-Sleep -Milliseconds "
                    "([int][Math]::Ceiling($player.NaturalDuration.TimeSpan.TotalMilliseconds))"
                )
                return [shell_exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script]

        available_players = [
            ("ffplay", ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", full_path]),
            ("mpv", ["mpv", "--no-video", "--really-quiet", full_path]),
            ("mpg123", ["mpg123", "-q", full_path]),
            ("cvlc", ["cvlc", "--play-and-exit", "--intf", "dummy", full_path]),
            ("play", ["play", "-q", full_path]),
        ]
        for exe_name, cmd_list in available_players:
            if shutil.which(exe_name):
                return cmd_list

        return None


# Keep backward compatibility with old import name
AudioPlayer = SoundPlayer