# src/utils.py
# src/utils.py
import re
from typing import Dict

# src/utils.py
import re
from typing import Dict

# === 掉落物中文映射（已有）===
DROP_NAME_MAP = {
    # Mod
    "DefaultModPickup": "随机 Mod",

    # 能量/生命
    "EnergyIncreaseSmall": "小型能量球",
    "EnergyIncreaseMedium": "中型能量球",
    "HealthIncreaseSmall": "小型生命球",
    "HealthIncreaseMedium": "中型生命球",

    # 资源
    "AlloyPlate": "合金板",
    "Ferrite": "铁氧体",
    "NanoSpores": "纳米孢子",
    "PolymerBundle": "聚合物捆",
    "Salvage": "打捞物",
    "OrokinCell": "Orokin 电池",
    "Fieldron": "菲德隆",
    "DetoniteInjector": "爆破注射器",
    "MutagenSample": "突变原样本",
    "NeuralSensors": "神经传感器",
    "ArgonCrystal": "氩结晶",

    # 现金
    "CreditsPickup": "现金",

    # 雕像
    "AyatanSculptureAnasa": "阿那萨雕像",
    "AyatanSculptureHuras": "胡拉斯雕像",
    "AyatanSculptureSantamu": "桑塔穆雕像",
}

# === 敌人中文映射（新增）===
ENEMY_NAME_MAP: Dict[str, str] = {
    # ========== Grineer ==========
    "Ballista": "弩炮",
    "Butcher": "屠夫",
    "Commander": "指挥官",
    "DargynPilot": "达金飞行员",
    "EliteLancer": "精英冲锋枪兵",
    "Flameblaster": "火焰喷射兵",
    "HeavyGunner": "重机枪兵",
    "HyekkaMaster": "鬣猫驯兽师",
    "Lancer": "冲锋枪兵",
    "ManicBombard": "狂躁轰击者",
    "ManicCutter": "狂躁切割者",
    "Napalm": "燃烧弹兵",
    "Nullifier": "驱魔者",
    "Razorback": "剃背恐鸟",
    "Riot": "暴徒",
    "Roller": "滚子",
    "Scorpion": "天蝎",
    "ShieldLancer": "盾枪兵",
    "Sniper": "狙击手",
    "Specter": "幽鬼",
    "Stalker": "追踪者",
    "TuskBallista": "巨牙弩炮",
    "TuskButcher": "巨牙屠夫",
    "TuskDargyn": "巨牙达金",
    "TuskHeavyGunner": "巨牙重机枪兵",
    "TuskLancer": "巨牙冲锋枪兵",
    "TuskScorpion": "巨牙天蝎",
    "TuskShieldLancer": "巨牙盾枪兵",

    # ========== Corpus ==========
    "AntiMOA": "反 MOA 机",
    "Bursa": "金流恐鸟",
    "Comba": "康巴",
    "CorpusTech": "科珀斯技师",
    "Crawler": "爬行者",
    "DenialBursa": "拒止金流恐鸟",
    "Detron": "德特昂枪兵",
    "EliteComba": "精英康巴",
    "GoxHunter": "戈克斯猎手",
    "Hyena": "鬣狗",
    "MOA": "MOA",
    "Osprey": "鱼鹰",
    "OxiumHyena": "氧化鬣狗",
    "Probe": "探测器",
    "RailgunMOA": "磁轨炮 MOA",
    "Scrambus": "干扰恐鸟",
    "ShockwaveMOA": "冲击波 MOA",
    "Supra": "苏普拉枪兵",

    # ========== Infested ==========
    "Ancient": "远古者",
    "Arachnoid": "蛛形机",
    "Boiler": "沸血者",
    "Charger": "冲锋者",
    "CrawlerInfested": "感染者爬行者",
    "DeimosBat": "蝠鲼（夜灵平野）",
    "DenMother": "育母",
    "Fungal": "真菌者",
    "Ghoul": "食尸鬼",
    "Juggernaut": "主宰",
    "Leech": "水蛭",
    "Mutalist": "异融者",
    "Necramech": "亡灵机甲",
    "Runner": "奔跳者",
    "ScorpionInfested": "感染者天蝎",
    "TarMorphid": "焦油变形虫",
    "ToxicAncient": "剧毒远古者",

    # ========== Corrupted / Orokin ==========
    "CorruptedButcher": "堕落屠夫",
    "CorruptedCommander": "堕落指挥官",
    "CorruptedHeavyGunner": "堕落重机枪兵",
    "CorruptedLancer": "堕落冲锋枪兵",
    "OrokinMoaBiped": "Orokin MOA（双足）",
    "OrokinMoaQuad": "Orokin MOA（四足）",

    # ========== 特殊任务 / 夜灵 ==========
    "VenusShockwaveBiped": "金星冲击波双足机",
    "VenusShotgunSpaceman": "金星霰弹枪兵",
    "ArachnoidCoolant": "冷却蛛形机",  # ← 你日志中的类型

    # ========== 默认兜底 ==========
    "Spaceman": "步枪兵",
    "RifleSpaceman": "步枪兵",
    "ShotgunSpaceman": "霰弹枪兵",
    "PistolSpaceman": "手枪兵",
    "Agent": "未知单位",
}


def get_chinese_drop_name(key: str) -> str:
    """将掉落物关键字转为中文名"""
    if key in DROP_NAME_MAP:
        return DROP_NAME_MAP[key]
    if "AyatanSculpture" in key:
        return "Ayatan 雕像"
    if "ModPickup" in key:
        return "Mod"
    if "EnergyIncrease" in key:
        return "能量球"
    if "HealthIncrease" in key:
        return "生命球"
    if "Credits" in key:
        return "现金"
    if any(r in key for r in
           ["Alloy", "Ferrite", "Nano", "Polymer", "Salvage", "Orokin", "Fieldron", "Detonite", "Mutagen", "Neural",
            "Argon"]):
        return "资源"
    return f"未知物品 ({key})"


def get_chinese_enemy_name(raw_key: str) -> str:
    """将敌人原始类型名（含数字后缀）转为中文名"""
    # 移除末尾数字（如 ArachnoidCoolantAgent1 → ArachnoidCoolantAgent）
    clean_key = re.sub(r'\d+$', '', raw_key)

    # 尝试精确匹配
    if clean_key in ENEMY_NAME_MAP:
        return ENEMY_NAME_MAP[clean_key]

    # 模糊匹配：移除常见后缀如 "Agent", "Spaceman"
    base_name = clean_key
    for suffix in ["Agent", "Spaceman", "Biped", "Quad"]:
        if base_name.endswith(suffix):
            base_name = base_name[:-len(suffix)]
            if base_name in ENEMY_NAME_MAP:
                return ENEMY_NAME_MAP[base_name]

    # 最终兜底
    return f"未知敌人 ({raw_key})"