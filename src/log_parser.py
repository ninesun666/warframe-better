# src/log_parser.py
import os
import re
import time
from collections import defaultdict
from datetime import datetime
from typing import Callable, Optional, Dict, Any

from .utils import get_chinese_drop_name

# === 日志路径自动探测 ===
def _detect_log_path() -> str:
    """自动检测 Warframe 日志文件路径"""
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Warframe\EE.log"),
        r"C:\Program Files (x86)\Steam\steamapps\common\Warframe\Warframe.log",
        os.path.expanduser("~/Library/Application Support/Warframe/EE.log"),  # macOS
        "/home/$USER/.local/share/Warframe/EE.log",  # Linux
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    # 默认返回平台版路径（即使不存在，后续会报错）
    return os.path.expandvars(r"%LOCALAPPDATA%\Warframe\EE.log")

LOG_PATH = _detect_log_path()

# === 正则表达式 ===
AGENT_PATTERN = re.compile(r'AI \[Info\]: OnAgentCreated /Npc/(\w+)\d+ Live \d+ Spawned \d+ Ticking \d+')
TELEPORT_PATTERN = re.compile(
    r'Script \[Info\]: TeleportAndFade\.lua:.*? ([\w]+) .*? -> Vector$$(.*?)$$'
)
# === 新增：保育动物相关正则 ===
CONSERVATION_ENCOUNTER_PATTERN = re.compile(
    r'AI \[Info\]: ENCMGR: Encounter /Lotus/Types/Gameplay/Conservation/([^/]+)/[^/]+Encounter started at [^ ]+ at pos $\(([^)]+)\)'
)
CONSERVATION_AGENT_PATTERN = re.compile(
    r'AI \[Info\]: OnAgentCreated /(Npc/Common(?:Female|Male)?(\w+)Agent\d+)'
)

# 进图检测：除了时间戳跳跃，也可通过首次大量 AI 日志判断
MISSION_START_THRESHOLD = 3  # 5 秒内出现 ≥3 个敌人视为新任务


class LogMonitor:
    def __init__(
            self,
            on_new_agent: Optional[Callable[[str], None]] = None,
            on_new_item: Optional[Callable[[Dict[str, Any]], None]] = None,
            on_mission_start: Optional[Callable[[], None]] = None,
            on_mission_end: Optional[Callable[[], None]] = None,
            on_conservation_refresh: Optional[Callable[[str, tuple], None]] = None,  # ← 新增
            debug: bool = False,  # ← 新增：是否打印原始日志
    ):
        # ... 其他初始化 ...
        self.debug = debug
        self.on_new_agent = on_new_agent or (lambda x: None)
        self.on_new_item = on_new_item or (lambda x: None)
        self.on_mission_start = on_mission_start or (lambda: None)
        self.on_mission_end = on_mission_end or (lambda: None)
        self.on_conservation_refresh = on_conservation_refresh or (lambda animal_type, pos: None)

        self.enemies = defaultdict(int)
        self.items = []
        self.mission_active = False
        self.last_timestamp = 0.0
        self._recent_agent_count = 0
        self._recent_agent_time = 0.0
        self._running = True

        self.conservation_active = True
        self.conservation_animals = []  # 存储 {type, agent, pos, time}

    def parse_vector(self, s: str) -> Optional[tuple]:
        """解析 Vector(x,y,z) 字符串为浮点元组"""
        try:
            parts = s.split(',')
            if len(parts) == 3:
                return tuple(float(x.strip()) for x in parts)
        except (ValueError, AttributeError):
            pass
        return None

    def reset_mission(self):
        """重置任务状态，触发开始回调"""
        self.enemies.clear()
        self.items.clear()
        self.mission_active = True
        self._recent_agent_count = 0
        self.on_mission_start()

    def detect_mission_start_by_activity(self, current_ts: float):
        """通过短时间内的敌人生成密度判断是否进图"""
        if not self.mission_active:
            if current_ts - self._recent_agent_time < 5.0:
                self._recent_agent_count += 1
            else:
                self._recent_agent_count = 1
                self._recent_agent_time = current_ts

            if self._recent_agent_count >= MISSION_START_THRESHOLD:
                self.reset_mission()

    def process_line(self, line: str):
        """处理单行日志"""
        try:
            # 提取时间戳
            ts_match = re.match(r'^(\d+\.\d+)', line)
            if not ts_match:
                return
            current_ts = float(ts_match.group(1))

            # 检测新任务：方式1 - 时间戳大幅跳变（>5000 单位 ≈ 新任务）
            if self.last_timestamp > 0 and current_ts - self.last_timestamp > 5000:
                self.reset_mission()
            self.last_timestamp = current_ts

            # 检测新任务：方式2 - 短时间内密集生成敌人（更可靠）
            if not self.mission_active:
                self.detect_mission_start_by_activity(current_ts)
                if not self.mission_active:
                    return  # 未进图，不处理后续

            # === 敌人生成 ===
            agent_match = AGENT_PATTERN.search(line)
            # 在 log_parser.py 的 process_line 方法中
            if agent_match:
                raw_npc = agent_match.group(1)
                npc_type = re.sub(r'\d+$', '', raw_npc)  # 归一化
                self.enemies[npc_type] += 1

                # 传递原始 key 给 GUI，由 GUI 决定显示英文还是中文
                self.on_new_agent(raw_npc)  # 或者传 npc_type
                # if self.debug:
                    # print(f"[DEBUG] 敌人: {npc_type} | 原始日志: {line.strip()}")

            # === 掉落物传送 ===
            tp_match = TELEPORT_PATTERN.search(line)
            if tp_match:
                raw_item_key = tp_match.group(1)
                vec_str = tp_match.group(2)
                pos = self.parse_vector(vec_str)
                if pos:
                    chinese_name = get_chinese_drop_name(raw_item_key)
                    item_data = {
                        'raw_key': raw_item_key,
                        'chinese_name': chinese_name,
                        'position': pos,
                        'timestamp': current_ts,
                    }
                    self.items.append(item_data)
                    self.on_new_item(item_data)
                    # if self.debug:
                    #     print(f"[DEBUG] 掉落: {chinese_name} ({raw_item_key}) @ {pos} | 原始日志: {line.strip()}")
            # === 保育动物：遭遇开始（刷新提示）===
            enc_match = CONSERVATION_ENCOUNTER_PATTERN.search(line)
            if enc_match:
                animal_type = enc_match.group(1)  # e.g., "OrokinKubrow"
                pos_str = enc_match.group(2)
                try:
                    pos = tuple(float(x.strip()) for x in pos_str.split(",")[:3])
                except:
                    pos = (0.0, 0.0, 0.0)

                # 标记保育任务激活
                self.conservation_active = True

                # 👉 触发“刷新小动物”回调！
                self.on_conservation_refresh(animal_type, pos)

                if self.debug:
                    print(f"[DEBUG] 保育动物刷新: {animal_type} @ {pos}")

            # === 保育动物：Agent 创建（记录个体）===
            agent_match_cons = CONSERVATION_AGENT_PATTERN.search(line)
            if agent_match_cons:
                full_path = agent_match_cons.group(1)  # e.g., "Npc/CommonFemaleOrokinKubrowAgent71"
                animal_name = agent_match_cons.group(2)  # e.g., "OrokinKubrow"

                self.conservation_animals.append({
                    "agent": full_path,
                    "type": animal_name,
                    "spawn_time": current_ts,
                    "position": None  # 可从 encounter 获取，此处暂不关联
                })
                # 👉 触发“刷新小动物”回调！
                self.on_conservation_refresh(animal_name, "")

                if self.debug:
                    print(f"[DEBUG] 保育动物实体创建: {animal_name} ({full_path})")

        except Exception as e:
            # 防止单行日志错误导致整个监控崩溃
            print(f"[LogParser] 处理日志行时出错: {e}")
            print(f"  原始行: {line[:100]}...")

    def start_monitoring(self):
        """启动日志监控（阻塞式）"""
        if not os.path.exists(LOG_PATH):
            raise FileNotFoundError(f"Warframe 日志文件未找到，请确认游戏正在运行。\n路径: {LOG_PATH}")

        print(f"[LogMonitor] 开始监控日志: {LOG_PATH}")
        if self.debug:
            print("[DEBUG] 调试模式已启用：将打印所有日志行")
        with open(LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(0, os.SEEK_END)
            while self._running:
                line = f.readline()
                if line:
                    # 👇 新增：debug 时打印原始日志 👇
                    if self.debug:
                        # 去掉末尾换行，避免 double \n
                        print(f"[RAW LOG] {line.rstrip()}")
                    # 👆 新增结束 👆
                    self.process_line(line)
                else:
                    time.sleep(0.5)

    def stop_monitoring(self):
        """停止监控（线程安全）"""
        self._running = False

    @property
    def mission_info(self) -> dict:
        """获取当前任务摘要信息（用于 GUI 显示）"""
        return {
            "active": self.mission_active,
            "enemy_count": sum(self.enemies.values()),
            "item_count": len(self.items),
            "enemies": dict(self.enemies),
            "latest_items": self.items[-10:] if self.items else [],
        }