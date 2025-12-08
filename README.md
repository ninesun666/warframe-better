## Warframe Log Monitor

本工具仅读取 `%LOCALAPPDATA%\Warframe\EE.log` 日志文件，用于实时显示任务中的敌人与物品生成。
- 不修改游戏文件
- 不连接网络
- 不收集任何用户数据
- 完全开源，安全透明


# pyinstaller --onedir --windowed --add-data "assets;assets" --icon=assets/icon.ico --name "WarframeMonitor" main.py
