# src/gui_app.py
import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
import threading
from .log_parser import LogMonitor
from .utils import get_chinese_enemy_name


class WarframeMonitorGUI:
    def __init__(self, root, debug=False):
        self.root = root
        self.root.title("Warframe 实时日志监控")
        self.root.geometry("550x450")
        self.root.iconbitmap(self._get_icon_path())  # 可选图标

        self.status_var = tk.StringVar(value="⏳ 等待进入任务...")
        tk.Label(root, textvariable=self.status_var, font=("Arial", 12)).pack(pady=5)

        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 敌人页
        enemy_frame = ttk.Frame(notebook)
        notebook.add(enemy_frame, text="👾 敌人")
        self.enemy_text = scrolledtext.ScrolledText(enemy_frame, font=("Consolas", 10))
        self.enemy_text.pack(fill=tk.BOTH, expand=True)

        # 物品页
        item_frame = ttk.Frame(notebook)
        notebook.add(item_frame, text="📦 物品")
        self.item_text = scrolledtext.ScrolledText(item_frame, font=("Consolas", 10))
        self.item_text.pack(fill=tk.BOTH, expand=True)

        # === 新增：保育页 ===
        conservation_frame = ttk.Frame(notebook)
        notebook.add(conservation_frame, text="🐾 保育")
        self.conservation_text = scrolledtext.ScrolledText(conservation_frame, font=("Consolas", 10))
        self.conservation_text.pack(fill=tk.BOTH, expand=True)
        self.conservation_animals = []  # 存储保育动物记录

        # 启动监控
        self.monitor = LogMonitor(
            on_new_agent=self._on_new_agent,
            on_new_item=self._on_new_item,
            on_mission_start=self._on_mission_start,
            on_conservation_refresh=self._on_conservation_refresh,  # ← 新增
            debug=debug
        )

        self.enemies = self.monitor.enemies
        self.items = self.monitor.items

        threading.Thread(target=self.monitor.start_monitoring, daemon=True).start()
        self._update_ui()

    def _get_icon_path(self):
        # 打包后也能找到图标
        import sys
        import os
        if getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, 'assets', 'icon.ico')
        else:
            return os.path.join('assets', 'icon.ico')

    def _on_mission_start(self):
        self.status_var.set(f"🚀 任务中 (开始于 {datetime.now().strftime('%H:%M:%S')})")

    def _on_new_agent(self,  raw_npc: str):
        chinese_name = get_chinese_enemy_name(raw_npc)
        # 更新 UI（你可能需要重构 enemy_text 的数据结构）
        self._update_ui()


    def _on_conservation_refresh(self, animal_type: str, position: tuple):
        """当保育动物刷新时调用"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        record = {
            "type": animal_type,
            "position": position,
            "time": timestamp
        }
        self.conservation_animals.append(record)

        # 👉 弹出桌面提示（可选）
        # self.root.bell()  # 发出提示音
        # self.status_var.set(f"🐾 {animal_type} 已刷新！{timestamp}")

        # 自动切换到保育页（可选，提升体验）
        # 注意：需通过 notebook widget 切换，但此处暂不持有引用
        # 如果需要自动切换，请保存 notebook 引用（见下方说明）

        # 触发 UI 更新
        self._update_ui()

    def _on_new_item(self, item_data):
        self._update_ui()

    def _update_ui(self):
        # 敌人（可选：也加中文映射，但敌人类型复杂，先保留英文）
        self.enemy_text.delete(1.0, tk.END)
        if self.enemies:
            for typ in sorted(self.enemies):
                self.enemy_text.insert(tk.END, f"• {typ}: {self.enemies[typ]}\n")
        else:
            self.enemy_text.insert(tk.END, "暂无敌人生成\n")

        # 掉落物（显示中文）
        self.item_text.delete(1.0, tk.END)
        if self.items:
            for item in list(self.items)[-15:]:  # 最近15个
                name = item['chinese_name']
                pos = item['position']
                self.item_text.insert(tk.END, f"• {name} @ {pos}\n")
        else:
            self.item_text.insert(tk.END, "暂无掉落物品\n")
        # === 保育动物 ===
        self.conservation_text.delete(1.0, tk.END)
        if self.conservation_animals:
            for rec in reversed(self.conservation_animals[-10:]):  # 显示最近10条
                self.conservation_text.insert(
                    tk.END,
                    f"• {rec['type']}  "
                    f"[{rec['time']}]\n"
                )
        else:
            self.conservation_text.insert(tk.END, "暂无保育动物生成\n")

        self.root.after(1000, self._update_ui)