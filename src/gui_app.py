# src/gui_app.py
import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
import threading
from .log_parser import LogMonitor
from .utils import get_chinese_enemy_name, get_chinese_conservation_name


class WarframeMonitorGUI:
    def __init__(self, root, debug=False):
        self.root = root
        self.root.title("Warframe 实时日志监控")
        self.root.geometry("550x450")
        self.root.iconbitmap(self._get_icon_path())  # 可选图标

        self.status_var = tk.StringVar(value="⏳ 等待进入任务...")
        tk.Label(root, textvariable=self.status_var, font=("Arial", 12)).pack(pady=5)
        
        # 地图信息显示
        self.level_var = tk.StringVar(value="📍 未进入地图")
        tk.Label(root, textvariable=self.level_var, font=("Arial", 10), fg="blue").pack(pady=2)

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

        # === 新增：奖励页 ===
        reward_frame = ttk.Frame(notebook)
        notebook.add(reward_frame, text="🎁 奖励")
        self.reward_text = scrolledtext.ScrolledText(reward_frame, font=("Consolas", 10))
        self.reward_text.pack(fill=tk.BOTH, expand=True)
        self._setup_context_menu(self.reward_text)
        self.rewards = []  # 存储奖励记录
        self.mission_success = None  # 任务成功状态

# 启动监控
        self.monitor = LogMonitor(
            on_new_agent=self._on_new_agent,
            on_new_item=self._on_new_item,
            on_mission_start=self._on_mission_start,
on_conservation_refresh=self._on_conservation_refresh,  # ← 新增
            on_reward_received=self._on_reward_received,  # ← 新增
            on_mission_complete=self._on_mission_complete,  # ← 新增
            on_level_loaded=self._on_level_loaded,  # ← 新增
            debug=debug
        )

        self.enemies = self.monitor.enemies
        self.items = self.monitor.items

        threading.Thread(target=self.monitor.start_monitoring, daemon=True).start()
        self._update_ui()

    def _setup_context_menu(self, text_widget):
        """为文本组件设置右键菜单，支持复制功能"""
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="复制 (Ctrl+C)", command=lambda: self._copy_text(text_widget))
        context_menu.add_separator()
        context_menu.add_command(label="全选 (Ctrl+A)", command=lambda: self._select_all(text_widget))
        context_menu.add_command(label="清空", command=lambda: self._clear_text(text_widget))
        
        def show_context_menu(event):
            context_menu.post(event.x_root, event.y_root)
        
        text_widget.bind("<Button-3>", show_context_menu)
        text_widget.bind("<Control-c>", lambda e: self._copy_text(text_widget))
        text_widget.bind("<Control-C>", lambda e: self._copy_text(text_widget))
        text_widget.bind("<Control-a>", lambda e: self._select_all(text_widget))
        text_widget.bind("<Control-A>", lambda e: self._select_all(text_widget))
    
    def _copy_text(self, text_widget):
        """复制选中的文本到剪贴板"""
        try:
            selected_text = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            pass
    
    def _select_all(self, text_widget):
        """全选文本"""
        text_widget.tag_add(tk.SEL, "1.0", tk.END)
        text_widget.mark_set(tk.INSERT, "1.0")
        text_widget.see(tk.INSERT)
    
    def _clear_text(self, text_widget):
        """清空文本"""
        text_widget.delete(1.0, tk.END)

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

    def _on_reward_received(self, reward_data):
        """当收到奖励时调用"""
        self.rewards.append(reward_data)
        self._update_ui()

    def _on_mission_complete(self, success):
        """当任务完成时调用"""
        self.mission_success = success
        status = "成功" if success else "失败"
        self.status_var.set(f"任务{status}！")
        self._update_ui()

    def _on_level_loaded(self, level_name):
        """当地图加载时调用"""
        # 简化地图名称显示
        display_name = level_name
        if len(level_name) > 50:
            display_name = level_name[:47] + "..."
        
        self.level_var.set(f"📍 {display_name}")
        self._update_ui()

    def _update_ui(self):
# 保存当前选中的文本
        try:
            enemy_selected = self.enemy_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            item_selected = self.item_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            conservation_selected = self.conservation_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            reward_selected = self.reward_text.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            enemy_selected = item_selected = conservation_selected = reward_selected = None
        
        # 敌人（显示中文）
        self.enemy_text.delete(1.0, tk.END)
        if self.enemies:
            for typ in sorted(self.enemies):
                chinese_name = get_chinese_enemy_name(typ)
                self.enemy_text.insert(tk.END, f"• {chinese_name}: {self.enemies[typ]}\n")
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
                chinese_name = get_chinese_conservation_name(rec['type'])
                self.conservation_text.insert(
                    tk.END,
                    f"• {chinese_name}  "
                    f"[{rec['time']}]\n"
                )
        else:
            self.conservation_text.insert(tk.END, "暂无保育动物生成\n")

        # === 奖励显示 ===
        self.reward_text.delete(1.0, tk.END)
        
        # 显示任务状态
        if self.mission_success is not None:
            status = "✅ 任务成功" if self.mission_success else "❌ 任务失败"
            self.reward_text.insert(tk.END, f"{status}\n")
            self.reward_text.insert(tk.END, "=" * 30 + "\n")
        
        # 显示奖励列表
        if self.rewards:
            for reward in reversed(self.rewards[-20:]):  # 显示最近20个奖励
                reward_type = reward['type']
                name = reward['name']
                amount = reward.get('amount', 1)
                time = reward['time']
                
                # 根据类型显示不同图标
                type_icons = {
                    'survival_cycle': '⏱️',
                    'item': '📦',
                    'extra': '⭐',
                    'credits': '💰',
                    'affinity': '⚡',
                    'extract': '🚪'
                }
                icon = type_icons.get(reward_type, '🎁')
                
                if amount > 1:
                    self.reward_text.insert(tk.END, f"{icon} {name} x{amount} [{time}]\n")
                else:
                    self.reward_text.insert(tk.END, f"{icon} {name} [{time}]\n")
        else:
            self.reward_text.insert(tk.END, "暂无奖励记录\n")

        # 恢复选中的文本（如果内容匹配）
        if enemy_selected:
            try:
                content = self.enemy_text.get(1.0, tk.END)
                if enemy_selected in content:
                    start = content.index(enemy_selected)
                    end = start + len(enemy_selected)
                    self.enemy_text.tag_add(tk.SEL, f"1.0 + {start} chars", f"1.0 + {end} chars")
            except:
                pass
        
        if item_selected:
            try:
                content = self.item_text.get(1.0, tk.END)
                if item_selected in content:
                    start = content.index(item_selected)
                    end = start + len(item_selected)
                    self.item_text.tag_add(tk.SEL, f"1.0 + {start} chars", f"1.0 + {end} chars")
            except:
                pass
        
        if conservation_selected:
            try:
                content = self.conservation_text.get(1.0, tk.END)
                if conservation_selected in content:
                    start = content.index(conservation_selected)
                    end = start + len(conservation_selected)
                    self.conservation_text.tag_add(tk.SEL, f"1.0 + {start} chars", f"1.0 + {end} chars")
            except:
                pass
        
        if reward_selected:
            try:
                content = self.reward_text.get(1.0, tk.END)
                if reward_selected in content:
                    start = content.index(reward_selected)
                    end = start + len(reward_selected)
                    self.reward_text.tag_add(tk.SEL, f"1.0 + {start} chars", f"1.0 + {end} chars")
            except:
                pass

        self.root.after(200, self._update_ui)