# install.ps1 — 一键安装 desktop-love-prank 技能
# 自动找到豆包技能目录，复制技能文件，提示重启

$ErrorActionPreference = "Stop"
$SkillName = "desktop-love-prank"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 目标：豆包 .user_skills 目录
$UserSkillsDir = Join-Path $env:LOCALAPPDATA "Doubao\User Data\Default\.doubao\agent_mode\workspace\.user_skills"

if (-not (Test-Path $UserSkillsDir)) {
    Write-Host "未找到豆包目录，请确认已安装电脑版豆包并打开过一次。" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

$TargetDir = Join-Path $UserSkillsDir $SkillName

# 复制
Write-Host "正在安装 $SkillName ..." -ForegroundColor Cyan
if (Test-Path $TargetDir) {
    Remove-Item $TargetDir -Recurse -Force
}
Copy-Item -Path $ScriptDir -Destination $TargetDir -Recurse -Force

Write-Host ""
Write-Host "安装完成！" -ForegroundColor Green
Write-Host "  技能位置：$TargetDir"
Write-Host ""
Write-Host "接下来："
Write-Host "  1. 关闭并重新打开豆包"
Write-Host "  2. 输入「放个猫咪爱心」即可触发"
Write-Host ""
Read-Host "按回车退出"
