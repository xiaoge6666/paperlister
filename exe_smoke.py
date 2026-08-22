# -*- coding: utf-8 -*-
"""打包版启动测试：启动 exe → 等 6s → 截图 → 退出。"""
import subprocess, time, os, sys
from pathlib import Path

exe = str(Path(__file__).resolve().parent / "dist" / "PaperLister.exe")
p = subprocess.Popen([exe])
time.sleep(7)
running = p.poll() is None
print("exe running:", running)
if not running:
    print("exit code:", p.returncode)
    sys.exit(1)

# 用 PowerShell 截图整个屏幕（窗口默认显示）
shot = str(Path(__file__).resolve().parent / "_exe_shot.png")
ps = f"""
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
$b = New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height)
$g = [System.Drawing.Graphics]::FromImage($b)
$g.CopyFromScreen(0,0,0,0,$b.Size)
$b.Save('{shot}')
"""
subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
print("screenshot saved")
p.terminate()
print("exe smoke OK")
