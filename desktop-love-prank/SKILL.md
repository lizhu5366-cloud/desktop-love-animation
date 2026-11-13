---
name: desktop-love-prank
description: 在用户 Windows 桌面上弹出全屏 GIF 爱心动画作为表白/惊喜/整蛊效果。先让一群猫咪 GIF 沿爱心曲线拼成一颗心，停留几秒后清空，再让 GIF 疯狂铺满整个屏幕，同时播放背景音乐。当用户说"放猫咪爱心""桌面表白""整蛊弹窗""爱心满屏""放个惊喜动画""月薪喵""送个爱心""秀个恩爱""给我整个活""撒狗粮""爱心雨""表白神器"或类似需求时使用。支持自定义文案、GIF 素材、背景音乐、爱心数量、铺满数量和速度。仅支持 Windows。
---

# Desktop Love Prank

在用户 Windows 桌面上播放 GIF 爱心动画：先拼爱心，再满屏刷屏，配背景音乐。

## 运行方式

**直接用启动脚本，一行命令搞定，自动找 Python、自动装 Pillow：**

```powershell
& "<skill_dir>\scripts\launch.ps1" --message "我真的特别爱你"
```

- 脚本在后台启动，不阻塞对话。
- 所有参数原样转发给 run.py。
- 用户没指定文案时，不传 `--message`，用默认值"我真的特别爱你"。

## 常用参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--message` | 我真的特别爱你 | 窗口标题文案 |
| `--gifs-dir` | assets/gifs | 自定义 GIF 目录 |
| `--music` | assets/music.mp3 | 自定义背景音乐路径 |
| `--no-sound` | 关 | 静音运行 |
| `--heart-count` | 70 | 拼爱心的 GIF 个数 |
| `--fill-count` | 350 | 满屏刷屏的 GIF 个数 |
| `--heart-interval` | 35 | 每个爱心点出现间隔（毫秒） |
| `--heart-hold` | 3000 | 爱心停留时间（毫秒） |
| `--fill-interval` | 10 | 满屏时每个窗口弹出间隔（毫秒） |
| `--no-topmost` | 关 | 不让窗口置顶 |

示例：
```powershell
# 默认效果
& "<skill_dir>\scripts\launch.ps1"

# 自定义文案
& "<skill_dir>\scripts\launch.ps1" --message "嫁给我吧"

# 更猛烈：爱心更多、铺满更快
& "<skill_dir>\scripts\launch.ps1" --heart-count 100 --fill-count 500 --fill-interval 5
```

## 关闭方式（必须告诉用户）

- 按 `Esc` 一键全部关闭
- 在任意 GIF 窗口上双击左键 / 右键关闭

## 注意事项

- 这个效果会瞬间铺满整个屏幕（默认 350 个窗口），**运行前必须提醒用户保存好手头工作**。
- 程序会置顶所有窗口，如果用户切不走，提示按 Esc。
- 不支持 macOS / Linux。
- 如果启动脚本报错找不到 Python，提示用户安装 Python 并勾选"Add to PATH"。
