#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巷道战场形态图生成器
基于 TerrainData JSON 生成包含战术意图的战场俯视图
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrow, Polygon
from matplotlib.lines import Line2D
import random
from datetime import datetime
from typing import List, Dict, Tuple, Any
import matplotlib.font_manager as fm

# 配置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'STHeiti', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# ==================== 配置参数 ====================
IMAGE_SIZE = 1600  # 图片尺寸（像素）
COORD_RANGE = 50  # 坐标范围 [-50, 50] 米
CIRCLE_RADII = [10, 20]  # 同心圆半径（米）
SPEED_NORMAL = (1, 5)  # 正常速度范围（米/秒）
SPEED_FAST = (10, 20)  # 快速移动范围（米/秒）

# 10种战术类型
TACTICS = [
    'encirclement',      # 包围
    'pincer',           # 钳形攻势
    'ambush',           # 伏击
    'retreat',          # 撤退
    'frontal_assault',  # 正面突击
    'flanking',         # 侧翼包抄
    'defensive',        # 防御阵型
    'guerrilla',        # 游击骚扰
    'pursuit',          # 追击
    'dispersed'         # 分散机动
]

# 战术中文名称映射
TACTIC_NAMES_CN = {
    'encirclement': '包围',
    'pincer': '钳形攻势',
    'ambush': '伏击',
    'retreat': '撤退',
    'frontal_assault': '正面突击',
    'flanking': '侧翼包抄',
    'defensive': '防御阵型',
    'guerrilla': '游击骚扰',
    'pursuit': '追击',
    'dispersed': '分散机动'
}


# ==================== TerrainData 解析器 ====================
class TerrainParser:
    """解析 TerrainData JSON 文件"""
    
    def __init__(self, json_file: str):
        with open(json_file, 'r', encoding='utf-8-sig') as f:
            self.data = json.load(f)
        
        self.buildings = self.data.get('buildings', [])
        self.alleys = self.data.get('alleys', [])
        self.obstacles = self.data.get('obstacles', [])
        self.terrain = self.data.get('terrain', {})
    
    def get_buildings(self) -> List[Dict]:
        """获取建筑物数据（简化为 x, z, width, depth）"""
        buildings_data = []
        for building in self.buildings:
            pos = building['position']
            size = building['size']
            buildings_data.append({
                'id': building['id'],
                'x': pos['x'],
                'z': pos['z'],
                'width': size['x'],
                'depth': size['y'],  # 注意：这里的y实际是z方向的尺寸
                'height': building.get('height', 0),
                'walls': building.get('walls', []),
                'doors': building.get('doors', []),
                'windows': building.get('windows', [])
            })
        return buildings_data
    
    def get_alleys(self) -> List[Dict]:
        """获取巷道数据"""
        alleys_data = []
        for alley in self.alleys:
            start = alley['start']
            end = alley['end']
            alleys_data.append({
                'id': alley['id'],
                'start_x': start['x'],
                'start_z': start['z'],
                'end_x': end['x'],
                'end_z': end['z'],
                'width': alley['width'],
                'length': alley['length']
            })
        return alleys_data
    
    def get_obstacles(self) -> List[Dict]:
        """获取障碍物数据"""
        obstacles_data = []
        for obstacle in self.obstacles:
            pos = obstacle['position']
            size = obstacle['size']
            obstacles_data.append({
                'id': obstacle['id'],
                'type': obstacle['type'],
                'x': pos['x'],
                'z': pos['z'],
                'width': size['x'],
                'depth': size['z'],
                'rotation': obstacle.get('rotation', 0)
            })
        return obstacles_data
    
    def is_inside_building(self, x: float, z: float) -> bool:
        """检查点是否在建筑物内部"""
        for building in self.buildings:
            pos = building['position']
            size = building['size']
            
            # 计算建筑物边界
            half_width = size['x'] / 2
            half_depth = size['y'] / 2
            
            if (abs(x - pos['x']) <= half_width and 
                abs(z - pos['z']) <= half_depth):
                return True
        return False


# ==================== 战术引擎 ====================
class TacticsEngine:
    """生成不同战术的敌人分布"""
    
    def __init__(self, terrain_parser: TerrainParser):
        self.terrain = terrain_parser
    
    def generate_enemies(self, tactic: str, num_enemies: int, speed_range: Tuple[float, float]) -> List[Dict]:
        """根据战术类型生成敌人分布"""
        method_name = f'_generate_{tactic}'
        if hasattr(self, method_name):
            return getattr(self, method_name)(num_enemies, speed_range)
        else:
            return self._generate_dispersed(num_enemies, speed_range)
    
    def _find_valid_position(self, x: float, z: float, enemy_type: str = 'soldier', 
                           existing_enemies: List[Dict] = None, max_attempts: int = 30) -> Tuple[float, float]:
        """找到不在建筑物内且不与其他敌人重叠的有效位置
        
        Args:
            x: 初始x坐标
            z: 初始z坐标
            enemy_type: 敌人类型 ('soldier' 或 'ifv')
            existing_enemies: 已有的敌人列表，用于碰撞检测
            max_attempts: 最大尝试次数
        
        Returns:
            有效的(x, z)坐标
        """
        if existing_enemies is None:
            existing_enemies = []
        
        # 定义敌人的碰撞半径（基于图标大小）
        # markersize 是点的大小，需要转换为地图坐标的实际半径
        # 假设markersize=14对应约2.5米，markersize=30对应约5米（进一步增大碰撞半径）
        soldier_radius = 2.5
        ifv_radius = 5.0
        
        # 获取障碍物列表（用于IFV碰撞检测）
        obstacles = self.terrain.get_obstacles()
        
        for _ in range(max_attempts):
            # 检查是否在建筑物内
            if not self.terrain.is_inside_building(x, z):
                # 对于步兵战车，需要更严格的检查（避免紧贴建筑物和障碍物）
                if enemy_type == 'ifv':
                    # 检查周围是否有足够空间（至少3米缓冲区）
                    safe = True
                    for dx in [-3, 0, 3]:
                        for dz in [-3, 0, 3]:
                            if self.terrain.is_inside_building(x + dx, z + dz):
                                safe = False
                                break
                        if not safe:
                            break
                    
                    # 检查是否与障碍物重叠
                    if safe:
                        for obstacle in obstacles:
                            ox, oz = obstacle['x'], obstacle['z']
                            o_width, o_depth = obstacle['width'], obstacle['depth']
                            
                            # 计算障碍物的边界
                            o_half_width = o_width / 2
                            o_half_depth = o_depth / 2
                            
                            # 使用圆形碰撞体与矩形障碍物的碰撞检测
                            # 找到矩形上距离圆心最近的点
                            closest_x = max(ox - o_half_width, min(x, ox + o_half_width))
                            closest_z = max(oz - o_half_depth, min(z, oz + o_half_depth))
                            
                            # 计算距离
                            distance = np.sqrt((x - closest_x)**2 + (z - closest_z)**2)
                            
                            # IFV需要与障碍物保持至少3米距离
                            if distance < ifv_radius:
                                safe = False
                                break
                    
                    if not safe:
                        x += random.uniform(-3, 3)
                        z += random.uniform(-3, 3)
                        x = max(-COORD_RANGE + 5, min(COORD_RANGE - 5, x))
                        z = max(-COORD_RANGE + 5, min(COORD_RANGE - 5, z))
                        continue
                
                # 检查是否与已有敌人重叠
                current_radius = ifv_radius if enemy_type == 'ifv' else soldier_radius
                overlap = False
                
                for existing in existing_enemies:
                    ex, ez = existing['x'], existing['z']
                    existing_radius = ifv_radius if existing['type'] == 'ifv' else soldier_radius
                    
                    # 计算距离
                    distance = np.sqrt((x - ex)**2 + (z - ez)**2)
                    
                    # 需要的最小距离（两个半径之和 + 1.0米安全间隙，增加安全距离）
                    min_distance = current_radius + existing_radius + 1.0
                    
                    if distance < min_distance:
                        overlap = True
                        break
                
                if not overlap:
                    return x, z
            
            # 如果位置无效，随机偏移
            x += random.uniform(-4, 4)
            z += random.uniform(-4, 4)
            # 确保在地图范围内
            x = max(-COORD_RANGE + 5, min(COORD_RANGE - 5, x))
            z = max(-COORD_RANGE + 5, min(COORD_RANGE - 5, z))
        
        return x, z  # 如果多次尝试失败，返回最后位置
    
    def _generate_encirclement(self, num_enemies: int, speed_range: Tuple[float, float]) -> List[Dict]:
        """包围战术：敌人均匀分布在用户周围"""
        enemies = []
        for i in range(num_enemies):
            angle = (360 / num_enemies) * i + random.uniform(-10, 10)
            angle_rad = np.radians(angle)
            distance = random.uniform(12, 22)
            
            x = distance * np.cos(angle_rad)
            z = distance * np.sin(angle_rad)
            
            # 随机选择敌人类型
            enemy_type = random.choice(['soldier', 'ifv'])
            x, z = self._find_valid_position(x, z, enemy_type, enemies)
            
            # 移动方向指向中心
            direction = (angle + 180) % 360
            
            # 生成速度，士兵最大速度限制为10m/s
            speed = random.uniform(*speed_range)
            if enemy_type == 'soldier':
                speed = min(speed, 10.0)
            
            enemies.append({
                'type': enemy_type,
                'x': x,
                'z': z,
                'speed': speed,
                'direction': direction
            })
        return enemies
    
    def _generate_pincer(self, num_enemies: int, speed_range: Tuple[float, float]) -> List[Dict]:
        """钳形攻势：左右两翼包抄"""
        enemies = []
        half = num_enemies // 2
        
        # 左翼
        for i in range(half):
            angle = random.uniform(135, 225)  # 左侧扇形
            angle_rad = np.radians(angle)
            distance = random.uniform(15, 25)
            
            x = distance * np.cos(angle_rad)
            z = distance * np.sin(angle_rad)
            
            enemy_type = random.choice(['soldier', 'ifv'])
            x, z = self._find_valid_position(x, z, enemy_type, enemies)
            
            # 向右前方移动
            direction = random.uniform(-30, 30)
            
            # 生成速度，士兵最大速度限制为10m/s
            speed = random.uniform(*speed_range)
            if enemy_type == 'soldier':
                speed = min(speed, 10.0)
            
            enemies.append({
                'type': enemy_type,
                'x': x,
                'z': z,
                'speed': speed,
                'direction': direction
            })
        
        # 右翼
        for i in range(num_enemies - half):
            angle = random.uniform(-45, 45)  # 右侧扇形
            angle_rad = np.radians(angle)
            distance = random.uniform(15, 25)
            
            x = distance * np.cos(angle_rad)
            z = distance * np.sin(angle_rad)
            
            enemy_type = random.choice(['soldier', 'ifv'])
            x, z = self._find_valid_position(x, z, enemy_type, enemies)
            
            # 向左前方移动
            direction = random.uniform(150, 210)
            
            # 生成速度，士兵最大速度限制为10m/s
            speed = random.uniform(*speed_range)
            if enemy_type == 'soldier':
                speed = min(speed, 10.0)
            
            enemies.append({
                'type': enemy_type,
                'x': x,
                'z': z,
                'speed': speed,
                'direction': direction
            })
        
        return enemies
    
    def _generate_ambush(self, num_enemies: int, speed_range: Tuple[float, float]) -> List[Dict]:
        """伏击战术：敌人隐藏在建筑和障碍物后"""
        enemies = []
        # 集中在某个方向（随机选择）
        ambush_angle = random.choice([0, 90, 180, 270])
        
        for i in range(num_enemies):
            angle = ambush_angle + random.uniform(-30, 30)
            angle_rad = np.radians(angle)
            distance = random.uniform(15, 25)
            
            x = distance * np.cos(angle_rad)
            z = distance * np.sin(angle_rad)
            
            enemy_type = random.choice(['soldier', 'ifv'])
            x, z = self._find_valid_position(x, z, enemy_type, enemies)
            
            # 静止或慢速移动
            direction = (angle + 180 + random.uniform(-20, 20)) % 360
            
            # 生成速度，士兵最大速度限制为10m/s
            speed = random.uniform(*speed_range) * 0.3  # 伏击时速度较慢
            if enemy_type == 'soldier':
                speed = min(speed, 10.0)
            
            enemies.append({
                'type': enemy_type,
                'x': x,
                'z': z,
                'speed': speed,
                'direction': direction
            })
        return enemies
    
    def _generate_retreat(self, num_enemies: int, speed_range: Tuple[float, float]) -> List[Dict]:
        """撤退战术：敌人向外逃离"""
        enemies = []
        for i in range(num_enemies):
            angle = (360 / num_enemies) * i + random.uniform(-15, 15)
            angle_rad = np.radians(angle)
            distance = random.uniform(18, 28)
            
            x = distance * np.cos(angle_rad)
            z = distance * np.sin(angle_rad)
            
            enemy_type = random.choice(['soldier', 'ifv'])
            x, z = self._find_valid_position(x, z, enemy_type, enemies)
            
            # 移动方向背离中心
            direction = angle % 360
            
            # 生成速度，士兵最大速度限制为10m/s
            speed = random.uniform(*speed_range) * 1.2  # 撤退速度较快
            if enemy_type == 'soldier':
                speed = min(speed, 10.0)
            
            enemies.append({
                'type': enemy_type,
                'x': x,
                'z': z,
                'speed': speed,
                'direction': direction
            })
        return enemies
    
    def _generate_frontal_assault(self, num_enemies: int, speed_range: Tuple[float, float]) -> List[Dict]:
        """正面突击：集中在前方"""
        enemies = []
        # 正面方向（假设为0度，即+X方向）
        front_angle = 0
        
        for i in range(num_enemies):
            angle = front_angle + random.uniform(-45, 45)
            angle_rad = np.radians(angle)
            
            # 排成多波次
            wave = i % 3
            distance = 15 + wave * 5 + random.uniform(-2, 2)
            
            x = distance * np.cos(angle_rad)
            z = distance * np.sin(angle_rad)
            
            enemy_type = random.choice(['soldier', 'ifv'])
            x, z = self._find_valid_position(x, z, enemy_type, enemies)
            
            # 直指中心
            direction = (angle + 180) % 360
            
            # 生成速度，士兵最大速度限制为10m/s
            speed = random.uniform(*speed_range)
            if enemy_type == 'soldier':
                speed = min(speed, 10.0)
            
            enemies.append({
                'type': enemy_type,
                'x': x,
                'z': z,
                'speed': speed,
                'direction': direction
            })
        return enemies
    
    def _generate_flanking(self, num_enemies: int, speed_range: Tuple[float, float]) -> List[Dict]:
        """侧翼包抄：从侧面包抄"""
        enemies = []
        # 随机选择左侧或右侧
        flank_side = random.choice([-90, 90])
        
        for i in range(num_enemies):
            angle = flank_side + random.uniform(-30, 30)
            angle_rad = np.radians(angle)
            distance = random.uniform(15, 25)
            
            x = distance * np.cos(angle_rad)
            z = distance * np.sin(angle_rad)
            
            enemy_type = random.choice(['soldier', 'ifv'])
            x, z = self._find_valid_position(x, z, enemy_type, enemies)
            
            # 斜向包抄
            if flank_side == -90:  # 左侧
                direction = random.uniform(30, 90)
            else:  # 右侧
                direction = random.uniform(270, 330)
            
            # 生成速度，士兵最大速度限制为10m/s
            speed = random.uniform(*speed_range)
            if enemy_type == 'soldier':
                speed = min(speed, 10.0)
            
            enemies.append({
                'type': enemy_type,
                'x': x,
                'z': z,
                'speed': speed,
                'direction': direction
            })
        return enemies
    
    def _generate_defensive(self, num_enemies: int, speed_range: Tuple[float, float]) -> List[Dict]:
        """防御阵型：依托掩体"""
        enemies = []
        # 获取障碍物位置作为防御点
        obstacles = self.terrain.get_obstacles()
        
        for i in range(num_enemies):
            enemy_type = random.choice(['soldier', 'ifv'])
            
            if obstacles and random.random() < 0.6:
                # 60%概率在障碍物附近
                obstacle = random.choice(obstacles)
                x = obstacle['x'] + random.uniform(-2, 2)
                z = obstacle['z'] + random.uniform(-2, 2)
            else:
                # 随机分布
                angle = random.uniform(0, 360)
                angle_rad = np.radians(angle)
                distance = random.uniform(12, 20)
                x = distance * np.cos(angle_rad)
                z = distance * np.sin(angle_rad)
            
            x, z = self._find_valid_position(x, z, enemy_type, enemies)
            
            # 朝向中心，低速或静止
            direction = np.degrees(np.arctan2(-z, -x))
            
            # 生成速度，士兵最大速度限制为10m/s
            speed = random.uniform(*speed_range) * 0.4  # 防御时速度很慢
            if enemy_type == 'soldier':
                speed = min(speed, 10.0)
            
            enemies.append({
                'type': enemy_type,
                'x': x,
                'z': z,
                'speed': speed,
                'direction': direction % 360
            })
        return enemies
    
    def _generate_guerrilla(self, num_enemies: int, speed_range: Tuple[float, float]) -> List[Dict]:
        """游击骚扰：分散不规则"""
        enemies = []
        for i in range(num_enemies):
            # 完全随机分布
            x = random.uniform(-COORD_RANGE + 5, COORD_RANGE - 5)
            z = random.uniform(-COORD_RANGE + 5, COORD_RANGE - 5)
            
            enemy_type = random.choice(['soldier', 'ifv'])
            x, z = self._find_valid_position(x, z, enemy_type, enemies)
            
            # 随机移动方向
            direction = random.uniform(0, 360)
            
            # 生成速度，士兵最大速度限制为10m/s
            speed = random.uniform(*speed_range)
            if enemy_type == 'soldier':
                speed = min(speed, 10.0)
            
            enemies.append({
                'type': enemy_type,
                'x': x,
                'z': z,
                'speed': speed,
                'direction': direction
            })
        return enemies
    
    def _generate_pursuit(self, num_enemies: int, speed_range: Tuple[float, float]) -> List[Dict]:
        """追击战术：从后方追赶"""
        enemies = []
        # 后方（假设为180度，即-X方向）
        rear_angle = 180
        
        for i in range(num_enemies):
            angle = rear_angle + random.uniform(-60, 60)
            angle_rad = np.radians(angle)
            distance = random.uniform(15, 25)
            
            x = distance * np.cos(angle_rad)
            z = distance * np.sin(angle_rad)
            
            enemy_type = random.choice(['soldier', 'ifv'])
            x, z = self._find_valid_position(x, z, enemy_type, enemies)
            
            # 向前追击
            direction = (angle + 180) % 360
            
            # 生成速度，士兵最大速度限制为10m/s
            speed = random.uniform(*speed_range) * 1.3  # 追击速度较快
            if enemy_type == 'soldier':
                speed = min(speed, 10.0)
            
            enemies.append({
                'type': enemy_type,
                'x': x,
                'z': z,
                'speed': speed,
                'direction': direction
            })
        return enemies
    
    def _generate_dispersed(self, num_enemies: int, speed_range: Tuple[float, float]) -> List[Dict]:
        """分散机动：均匀分散"""
        enemies = []
        for i in range(num_enemies):
            angle = (360 / num_enemies) * i + random.uniform(-20, 20)
            angle_rad = np.radians(angle)
            distance = random.uniform(15, 25)
            
            x = distance * np.cos(angle_rad)
            z = distance * np.sin(angle_rad)
            
            enemy_type = random.choice(['soldier', 'ifv'])
            x, z = self._find_valid_position(x, z, enemy_type, enemies)
            
            # 辐射状移动
            direction = angle + random.uniform(-30, 30)
            
            # 生成速度，士兵最大速度限制为10m/s
            speed = random.uniform(*speed_range)
            if enemy_type == 'soldier':
                speed = min(speed, 10.0)
            
            enemies.append({
                'type': enemy_type,
                'x': x,
                'z': z,
                'speed': speed,
                'direction': direction % 360
            })
        return enemies


# ==================== 2D 渲染器 ====================
class BattlefieldRenderer:
    """渲染战场俯视图"""
    
    def __init__(self, terrain_parser: TerrainParser):
        self.terrain = terrain_parser
        self.fig_size = (16, 16)
        self.dpi = 100
    
    def render(self, enemies: List[Dict], title: str, filename: str):
        """渲染完整的战场图"""
        fig, ax = plt.subplots(figsize=self.fig_size, dpi=self.dpi)
        
        # 设置坐标范围
        ax.set_xlim(-COORD_RANGE, COORD_RANGE)
        ax.set_ylim(-COORD_RANGE, COORD_RANGE)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.set_facecolor('#f0f0f0')
        
        # 1. 绘制巷道
        self._draw_alleys(ax)
        
        # 2. 绘制建筑物
        self._draw_buildings(ax)
        
        # 3. 绘制障碍物
        self._draw_obstacles(ax)
        
        # 4. 绘制同心圆
        for radius in CIRCLE_RADII:
            circle = Circle((0, 0), radius, fill=False, edgecolor='blue', 
                          linestyle='--', linewidth=2, alpha=0.6)
            ax.add_patch(circle)
        
        # 5. 绘制用户位置
        ax.plot(0, 0, marker='*', color='red', markersize=20, 
               markeredgecolor='darkred', markeredgewidth=2, label='Player')
        
        # 6. 绘制敌人
        self._draw_enemies(ax, enemies)
        
        # 7. 添加图例（使用更小尺寸避免遮挡）
        legend_elements = [
            Line2D([0], [0], marker='*', color='w', markerfacecolor='red', 
                   markersize=10, label='Player', markeredgecolor='darkred', markeredgewidth=1.5),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='orangered', 
                   markersize=9, label='Soldier (ID)', markeredgecolor='darkred', markeredgewidth=1.5),
            Line2D([0], [0], marker='s', color='w', markerfacecolor='purple', 
                   markersize=11, label='IFV (ID)', markeredgecolor='darkviolet', markeredgewidth=1.5),
            Rectangle((0, 0), 1, 1, facecolor='dimgray', edgecolor='black', 
                     alpha=0.7, linewidth=1.5, label='Building'),
            Rectangle((0, 0), 1, 1, facecolor='lightgray', alpha=0.5, 
                     linewidth=1, label='Alley'),
            Rectangle((0, 0), 1, 1, facecolor='saddlebrown', alpha=0.8, 
                     label='Cover'),
            Rectangle((0, 0), 1, 1, facecolor='black', alpha=0.9, 
                     label='Barrier'),
            Rectangle((0, 0), 1, 1, facecolor='darkblue', alpha=0.8, 
                     label='Vehicle')
        ]
        
        ax.legend(handles=legend_elements, loc='upper right', fontsize=8, 
                 framealpha=0.9, edgecolor='black', fancybox=True)
        
        # 设置标题和标签
        ax.set_xlabel('X Coordinate (m)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Z Coordinate (m)', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        print(f"✓ 已生成: {filename}")
    
    def _draw_alleys(self, ax):
        """绘制巷道"""
        alleys = self.terrain.get_alleys()
        for alley in alleys:
            # 计算巷道的四个角点
            start_x, start_z = alley['start_x'], alley['start_z']
            end_x, end_z = alley['end_x'], alley['end_z']
            width = alley['width']
            
            # 计算垂直方向
            dx = end_x - start_x
            dz = end_z - start_z
            length = np.sqrt(dx**2 + dz**2)
            if length > 0:
                perp_x = -dz / length * width / 2
                perp_z = dx / length * width / 2
                
                # 四个角点
                points = [
                    [start_x + perp_x, start_z + perp_z],
                    [start_x - perp_x, start_z - perp_z],
                    [end_x - perp_x, end_z - perp_z],
                    [end_x + perp_x, end_z + perp_z]
                ]
                
                rect = Polygon(points, facecolor='lightgray', edgecolor='gray', 
                             alpha=0.5, linewidth=1)
                ax.add_patch(rect)
    
    def _draw_buildings(self, ax):
        """绘制建筑物"""
        buildings = self.terrain.get_buildings()
        for building in buildings:
            x, z = building['x'], building['z']
            width, depth = building['width'], building['depth']
            
            # 绘制建筑物轮廓
            rect = Rectangle((x - width/2, z - depth/2), width, depth,
                           facecolor='dimgray', edgecolor='black', 
                           alpha=0.7, linewidth=2)
            ax.add_patch(rect)
            
            # 标注建筑物编号（增大字体）
            ax.text(x, z, f"B{building['id']}", 
                   ha='center', va='center', fontsize=14, 
                   color='white', fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.5))
    
    def _draw_obstacles(self, ax):
        """绘制障碍物"""
        obstacles = self.terrain.get_obstacles()
        for obstacle in obstacles:
            x, z = obstacle['x'], obstacle['z']
            width, depth = obstacle['width'], obstacle['depth']
            obs_type = obstacle['type']
            rotation = obstacle['rotation']
            
            if obs_type == 'Cover':
                # 掩体：棕色三角形
                size = max(width, depth)
                triangle = np.array([[x, z + size/2], 
                                    [x - size/2, z - size/2],
                                    [x + size/2, z - size/2]])
                ax.fill(triangle[:, 0], triangle[:, 1], 
                       color='saddlebrown', alpha=0.8)
            elif obs_type == 'Barrier':
                # 路障：黑色矩形
                rect = Rectangle((x - width/2, z - depth/2), width, depth,
                               facecolor='black', alpha=0.9)
                ax.add_patch(rect)
            elif obs_type == 'Vehicle':
                # 车辆：深蓝色矩形（带旋转）
                rect = Rectangle((x - width/2, z - depth/2), width, depth,
                               facecolor='darkblue', alpha=0.8,
                               angle=rotation)
                ax.add_patch(rect)
    
    def _draw_enemies(self, ax, enemies: List[Dict]):
        """绘制敌人及其信息"""
        for i, enemy in enumerate(enemies):
            x, z = enemy['x'], enemy['z']
            enemy_type = enemy['type']
            speed = enemy['speed']
            direction = enemy['direction']
            
            # 绘制敌人图标（IFV显著增大）
            if enemy_type == 'soldier':
                # 士兵：橙红色圆圈
                ax.plot(x, z, 'o', color='orangered', markersize=14, 
                       markeredgecolor='darkred', markeredgewidth=2)
            else:  # ifv (步兵战车)
                # IFV：紫色方块（30像素）
                ax.plot(x, z, 's', color='purple', markersize=30,
                       markeredgecolor='darkviolet', markeredgewidth=2.5)
            
            # 在图标内部标注编号（白色文字）
            enemy_number = i + 1
            ax.text(x, z, str(enemy_number),
                   fontsize=8, fontweight='bold',
                   ha='center', va='center',
                   color='white',
                   family='monospace')
            
            # 绘制移动方向箭头
            arrow_length = 3.5
            dir_rad = np.radians(direction)
            dx = arrow_length * np.cos(dir_rad)
            dz = arrow_length * np.sin(dir_rad)
            
            ax.arrow(x, z, dx, dz, head_width=1.2, head_length=1,
                    fc='yellow', ec='orange', alpha=0.7, linewidth=2)
            
            # 在箭头末端标注速度（黑色背景，黄色文字）
            arrow_end_x = x + dx
            arrow_end_z = z + dz
            speed_text = f"{speed:.1f}"
            ax.text(arrow_end_x, arrow_end_z, speed_text,
                   fontsize=7, fontweight='bold',
                   ha='center', va='center',
                   color='yellow',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='black', 
                           edgecolor='orange', linewidth=1, alpha=0.8),
                   family='monospace')
    


# ==================== 主生成器 ====================
def generate_all_images(terrain_file: str, output_dir: str):
    """生成所有30张图片"""
    
    print("\n" + "=" * 60)
    print("巷道战场形态图生成器")
    print("=" * 60)
    print(f"地形文件: {terrain_file}")
    print(f"输出目录: {output_dir}")
    print(f"战术类型: {len(TACTICS)}种")
    print(f"总图片数: {len(TACTICS) * 3}张")
    print("=" * 60)
    
    # 1. 解析地形
    print("\n[1/4] 解析地形数据...")
    terrain_parser = TerrainParser(terrain_file)
    print(f"  ✓ 建筑物: {len(terrain_parser.buildings)}栋")
    print(f"  ✓ 巷道: {len(terrain_parser.alleys)}条")
    print(f"  ✓ 障碍物: {len(terrain_parser.obstacles)}个")
    
    # 2. 初始化战术引擎和渲染器
    print("\n[2/4] 初始化战术引擎和渲染器...")
    tactics_engine = TacticsEngine(terrain_parser)
    renderer = BattlefieldRenderer(terrain_parser)
    print("  ✓ 战术引擎已就绪")
    print("  ✓ 渲染器已就绪")
    
    # 3. 生成图片
    print("\n[3/4] 生成战场图片...")
    all_data = []
    
    image_types = [
        ('type1', 3, SPEED_NORMAL, 'Type1_Sparse'),
        ('type2', 30, SPEED_NORMAL, 'Type2_Dense'),
        ('type3', 30, SPEED_FAST, 'Type3_Fast')
    ]
    
    for type_name, num_enemies, speed_range, type_label in image_types:
        print(f"\n  生成 {type_name} 类型图片（{num_enemies}个敌人）...")
        
        for idx, tactic in enumerate(TACTICS, 1):
            tactic_cn = TACTIC_NAMES_CN[tactic]
            
            # 生成敌人
            enemies = tactics_engine.generate_enemies(tactic, num_enemies, speed_range)
            
            # 为每个敌人添加唯一编号（从1开始）
            for i, enemy in enumerate(enemies, 1):
                enemy['id'] = i
            
            # 生成文件名和标题（英文标题避免字体问题）
            filename = os.path.join(output_dir, 
                                   f'{type_name}_tactic_{tactic}_{idx:02d}.png')
            title = f'{type_label} - Tactic: {tactic.upper()} ({tactic_cn}) - {num_enemies} Enemies'
            
            # 渲染图片
            renderer.render(enemies, title, filename)
            
            # 保存数据
            image_data = {
                'imageId': f'{type_name}_{tactic}_{idx:02d}',
                'filename': os.path.basename(filename),
                'type': type_label,
                'tacticType': tactic,
                'tacticNameCN': tactic_cn,
                'enemyCount': num_enemies,
                'speedRange': {'min': speed_range[0], 'max': speed_range[1]},
                'enemies': enemies
            }
            all_data.append(image_data)
    
    print(f"\n  ✓ 共生成 {len(all_data)} 张图片")
    
    # 4. 导出JSON数据
    print("\n[4/4] 导出JSON数据...")
    export_data = {
        'metadata': {
            'version': '2.0',
            'generatedAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'terrainFile': os.path.basename(terrain_file),
            'coordinateSystem': 'xOz',
            'imageSize': IMAGE_SIZE,
            'coordinateRange': COORD_RANGE,
            'circleRadii': CIRCLE_RADII,
            'tactics': TACTICS,
            'totalImages': len(all_data)
        },
        'terrain': {
            'buildings': terrain_parser.get_buildings(),
            'alleys': terrain_parser.get_alleys(),
            'obstacles': terrain_parser.get_obstacles()
        },
        'images': all_data
    }
    
    json_file = os.path.join(output_dir, 'urban_battlefield_data.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ 数据已保存: {json_file}")
    
    print("\n" + "=" * 60)
    print("✅ 所有任务完成！")
    print(f"总计生成: {len(all_data)}张图片 + 1个JSON数据文件")
    print(f"保存位置: {output_dir}")
    print("=" * 60)
    
    return export_data


def main():
    """主函数"""
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 地形文件路径
    terrain_file = os.path.join(script_dir, 'TerrainData_20251219_191755.json')
    
    # 输出目录
    output_dir = script_dir
    
    # 检查地形文件是否存在
    if not os.path.exists(terrain_file):
        print(f"错误: 找不到地形文件 {terrain_file}")
        return
    
    # 生成所有图片
    generate_all_images(terrain_file, output_dir)


if __name__ == '__main__':
    main()

