#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
战况播报生成器
根据战场数据生成军事风格的战况播报
"""

import json
import math

def calculate_distance(x, z):
    """计算到中心点的距离"""
    return math.sqrt(x**2 + z**2)

def calculate_clock_position(x, z):
    """计算时钟方位（12点为正北/+Z，顺时针）"""
    angle = math.degrees(math.atan2(x, z))
    if angle < 0:
        angle += 360
    hour = int((angle + 15) / 30) % 12
    if hour == 0:
        hour = 12
    return hour

def get_movement_description(speed, direction, x, z):
    """根据速度和方向描述动作"""
    # 计算是否指向中心
    to_center_angle = math.degrees(math.atan2(-z, -x))
    if to_center_angle < 0:
        to_center_angle += 360
    
    angle_diff = abs(direction - to_center_angle)
    if angle_diff > 180:
        angle_diff = 360 - angle_diff
    
    is_approaching = angle_diff < 45
    is_retreating = angle_diff > 135
    
    # 速度描述
    if speed < 1:
        speed_desc = "缓慢移动"
    elif speed < 3:
        speed_desc = "低速前进"
    elif speed < 5:
        speed_desc = "机动"
    elif speed < 8:
        speed_desc = "快速突进"
    else:
        speed_desc = "高速突击"
    
    # 方向描述
    if is_approaching:
        return f"{speed_desc}向我方逼近"
    elif is_retreating:
        return f"{speed_desc}撤离"
    else:
        dir_angle = direction % 360
        if 337.5 <= dir_angle or dir_angle < 22.5:
            dir_str = "向东"
        elif 22.5 <= dir_angle < 67.5:
            dir_str = "向东北"
        elif 67.5 <= dir_angle < 112.5:
            dir_str = "向北"
        elif 112.5 <= dir_angle < 157.5:
            dir_str = "向西北"
        elif 157.5 <= dir_angle < 202.5:
            dir_str = "向西"
        elif 202.5 <= dir_angle < 247.5:
            dir_str = "向西南"
        elif 247.5 <= dir_angle < 292.5:
            dir_str = "向南"
        else:
            dir_str = "向东南"
        return f"{speed_desc}{dir_str}机动"

def get_tactic_description(tactic):
    """获取战术描述"""
    tactic_map = {
        'encirclement': '包围态势',
        'pincer': '钳形攻势',
        'ambush': '伏击阵型',
        'retreat': '撤退态势',
        'frontal_assault': '正面突击',
        'flanking': '侧翼包抄',
        'defensive': '防御阵型',
        'guerrilla': '游击骚扰',
        'pursuit': '追击态势',
        'dispersed': '分散机动'
    }
    return tactic_map.get(tactic, '未知战术')

def get_unit_type(soldiers, uavs):
    """判断单位类型"""
    if uavs > 0 and soldiers > 0:
        return "空地协同分队"
    elif uavs > 0 and soldiers == 0:
        return "无人机侦察组"
    else:
        return "步兵班"

def generate_template1_broadcast(data):
    """模板一：简单场景（≤10个目标）"""
    enemies = data['enemies']
    total = len(enemies)
    soldiers = sum(1 for e in enemies if e['type'] == 'soldier')
    uavs = total - soldiers
    unit_type = get_unit_type(soldiers, uavs)
    tactic = get_tactic_description(data['tacticType'])
    
    # 按距离排序
    enemies_sorted = sorted(enemies, key=lambda e: calculate_distance(e['x'], e['z']))
    
    broadcast = f"共发现{total}个目标，识别为{uavs}架无人机与{soldiers}名士兵，判定为{unit_type}，呈{tactic}。"
    
    for enemy in enemies_sorted:
        dist = int(calculate_distance(enemy['x'], enemy['z']))
        clock = calculate_clock_position(enemy['x'], enemy['z'])
        enemy_type = "无人机" if enemy['type'] == 'uav' else "士兵"
        action = get_movement_description(enemy['speed'], enemy['direction'], enemy['x'], enemy['z'])
        
        broadcast += f"目标{enemy['id']}号{enemy_type}位于{clock}点钟方向{dist}米处，正{action}；"
    
    return broadcast.rstrip('；') + "。"

def generate_template2_broadcast(data):
    """模板二：复杂场景（>10个目标）"""
    enemies = data['enemies']
    total = len(enemies)
    soldiers = sum(1 for e in enemies if e['type'] == 'soldier')
    uavs = total - soldiers
    unit_type = get_unit_type(soldiers, uavs)
    tactic = get_tactic_description(data['tacticType'])
    
    # 计算距离
    for enemy in enemies:
        enemy['distance'] = calculate_distance(enemy['x'], enemy['z'])
    
    enemies_sorted = sorted(enemies, key=lambda e: e['distance'])
    
    # 判断警报等级
    min_dist = enemies_sorted[0]['distance']
    max_speed = max(e['speed'] for e in enemies)
    alert_level = "一级警报" if min_dist < 10 or max_speed > 10 else "警报"
    
    # 核心威胁（最近的2-3个）
    core_threats = enemies_sorted[:min(3, total)]
    
    # 计算主力方位（大多数敌人的平均方位）
    avg_x = sum(e['x'] for e in enemies) / total
    avg_z = sum(e['z'] for e in enemies) / total
    main_clock = calculate_clock_position(avg_x, avg_z)
    
    # 判断整体动向
    approaching_count = 0
    for e in enemies:
        to_center_angle = math.degrees(math.atan2(-e['z'], -e['x']))
        if to_center_angle < 0:
            to_center_angle += 360
        angle_diff = abs(e['direction'] - to_center_angle)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        if angle_diff < 45:
            approaching_count += 1
    
    if approaching_count > total * 0.6:
        main_action = "协同向我方压进"
    elif approaching_count < total * 0.3:
        main_action = "全线撤退"
    else:
        main_action = "构建火力网"
    
    # 生成播报
    broadcast = f"{alert_level}！接触大批敌军，当前战场共发现{total}个目标。"
    broadcast += f"装备识别为{uavs}架无人机与{soldiers}名士兵，判定为{unit_type}，目前呈{tactic}。"
    
    # 核心威胁
    threat_ids = "、".join([f"{e['id']}号" for e in core_threats])
    threat_dist = int(core_threats[0]['distance'])
    threat_clock = calculate_clock_position(core_threats[0]['x'], core_threats[0]['z'])
    threat_desc = "突入核心圈" if threat_dist < 10 else "逼近警戒线"
    
    broadcast += f"核心威胁位于{threat_clock}点钟方向，其中目标{threat_ids}已{threat_desc}，距离约{threat_dist}米；"
    
    # 主力集群
    min_main_dist = int(enemies_sorted[3]['distance']) if len(enemies_sorted) > 3 else threat_dist
    max_main_dist = int(enemies_sorted[-1]['distance'])
    broadcast += f"主力集群密集分布于{main_clock}点钟方向{min_main_dist}-{max_main_dist}米范围，正{main_action}。"
    
    return broadcast

def generate_all_broadcasts(json_file, output_file):
    """生成所有图片的播报"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    broadcasts = []
    
    for image_data in data['images']:
        image_id = image_data['imageId']
        enemy_count = image_data['enemyCount']
        
        # 根据敌人数量选择模板
        if enemy_count <= 10:
            broadcast = generate_template1_broadcast(image_data)
        else:
            broadcast = generate_template2_broadcast(image_data)
        
        broadcasts.append({
            'imageId': image_id,
            'filename': image_data['filename'],
            'tactic': image_data['tacticType'],
            'tacticNameCN': image_data['tacticNameCN'],
            'enemyCount': enemy_count,
            'broadcast': broadcast,
            'length': len(broadcast)
        })
    
    # 保存结果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(broadcasts, f, indent=2, ensure_ascii=False)
    
    # 打印播报
    print("\n" + "=" * 80)
    print("战况播报生成完成")
    print("=" * 80)
    for item in broadcasts:
        print(f"\n【{item['filename']}】")
        print(f"战术：{item['tacticNameCN']} | 敌人数量：{item['enemyCount']} | 字数：{item['length']}")
        print(f"{item['broadcast']}")
        print("-" * 80)
    
    return broadcasts

if __name__ == '__main__':
    json_file = 'urban_battlefield_data.json'
    output_file = 'battlefield_broadcasts.json'
    generate_all_broadcasts(json_file, output_file)

