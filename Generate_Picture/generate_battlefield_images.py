#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
战场形态图生成器
生成三种类型的战场图片，每种10张
同时导出JSON数据文件供C#读取
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrow
import random
import json

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 配置参数
IMAGE_SIZE = 1200  # 图片尺寸（像素）
COORD_RANGE = 30   # 坐标范围（米）
CIRCLE_RADII = [10, 20]  # 同心圆半径（米）

# 敌人类型
ENEMY_TYPES = ['soldier', 'drone']

# 速度范围（米/秒）
SPEED_NORMAL = (1, 5)
SPEED_FAST = (10, 20)


def generate_enemy(coord_range, speed_range, enemy_type=None):
    """
    随机生成一个敌人的数据
    
    Args:
        coord_range: 坐标范围（米）
        speed_range: 速度范围（最小值，最大值）
        enemy_type: 敌人类型 'soldier' 或 'drone'，None则随机
    
    Returns:
        dict: 包含敌人所有信息的字典
    """
    if enemy_type is None:
        enemy_type = random.choice(ENEMY_TYPES)
    
    # 随机生成坐标（避免太靠近中心）
    min_dist = 2  # 最小距离（米）
    while True:
        x = random.uniform(-coord_range, coord_range)
        y = random.uniform(-coord_range, coord_range)
        dist = np.sqrt(x**2 + y**2)
        if dist >= min_dist and dist <= coord_range:
            break
    
    # 随机生成速度和方向
    speed = random.uniform(speed_range[0], speed_range[1])
    direction = random.uniform(0, 360)  # 度数
    
    return {
        'type': enemy_type,
        'x': x,
        'y': y,
        'speed': speed,
        'direction': direction
    }


def draw_battlefield(enemies, filename, title):
    """
    绘制战场图
    
    Args:
        enemies: 敌人数据列表
        filename: 保存文件名
        title: 图片标题
    """
    # 创建图形
    fig, ax = plt.subplots(figsize=(12, 12), dpi=100)
    
    # 设置坐标轴范围和比例
    ax.set_xlim(-COORD_RANGE, COORD_RANGE)
    ax.set_ylim(-COORD_RANGE, COORD_RANGE)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # 设置标签
    ax.set_xlabel('X 坐标 (米)', fontsize=12)
    ax.set_ylabel('Y 坐标 (米)', fontsize=12)
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    
    # 绘制同心圆
    for radius in CIRCLE_RADII:
        circle = Circle((0, 0), radius, fill=False, 
                       edgecolor='gray', linestyle='--', 
                       linewidth=2, alpha=0.5)
        ax.add_patch(circle)
        # 标注半径
        ax.text(radius * 0.707, radius * 0.707, f'{radius}m', 
               fontsize=10, color='gray', ha='center')
    
    # 绘制用户位置（中心）
    ax.plot(0, 0, marker='*', markersize=30, color='blue', 
           markeredgecolor='darkblue', markeredgewidth=2, 
           label='用户位置', zorder=10)
    ax.text(0, -2, '用户', fontsize=11, ha='center', 
           color='blue', fontweight='bold')
    
    # 绘制敌人
    for i, enemy in enumerate(enemies):
        x, y = enemy['x'], enemy['y']
        enemy_type = enemy['type']
        speed = enemy['speed']
        direction = enemy['direction']
        
        # 根据类型选择样式（颜色对比更明显）
        if enemy_type == 'soldier':
            marker = 'o'  # 圆形
            color = 'orangered'  # 橙红色
            edge_color = 'darkred'
            size = 150
            label = '士兵'
        else:  # drone
            marker = 's'  # 方形
            color = 'purple'  # 紫色
            edge_color = 'darkviolet'
            size = 200
            label = '坦克'
        
        # 绘制敌人标记
        ax.scatter(x, y, marker=marker, s=size, c=color, 
                  edgecolors=edge_color, linewidths=2, 
                  alpha=0.9, zorder=5)
        
        # 绘制移动方向箭头
        arrow_length = 3  # 箭头长度（米）
        direction_rad = np.radians(direction)
        dx = arrow_length * np.cos(direction_rad)
        dy = arrow_length * np.sin(direction_rad)
        
        arrow = FancyArrow(x, y, dx, dy, 
                          width=0.5, head_width=1.5, head_length=1,
                          fc=color, ec='black', alpha=0.7, zorder=4)
        ax.add_patch(arrow)
        
        # 添加信息标注（带引导线）
        # 计算标注位置（避免与箭头重叠）
        label_offset_x = -5 if x > 0 else 5
        label_offset_y = 3
        label_x = x + label_offset_x
        label_y = y + label_offset_y
        
        # 绘制从敌人位置到标注框的引导线
        ax.plot([x, label_x], [y, label_y], 
               color=color, linestyle='-', linewidth=1, 
               alpha=0.6, zorder=3)
        
        info_text = f'{label}\n({x:.1f}, {y:.1f})m\n{speed:.1f}m/s\n{direction:.0f}°'
        ax.text(label_x, label_y, info_text,
               fontsize=8, ha='right' if x > 0 else 'left',
               va='bottom', bbox=dict(boxstyle='round,pad=0.3', 
               facecolor='white', edgecolor=edge_color, 
               linewidth=1.5, alpha=0.9))
    
    # 添加图例
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='*', color='w', markerfacecolor='blue', 
               markersize=15, label='用户位置', markeredgecolor='darkblue'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='orangered', 
               markersize=10, label='士兵', markeredgecolor='darkred', markeredgewidth=2),
        Line2D([0], [0], marker='s', color='w', markerfacecolor='purple', 
               markersize=10, label='坦克', markeredgecolor='darkviolet', markeredgewidth=2)
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10, framealpha=0.9)
    
    # 添加统计信息
    soldier_count = sum(1 for e in enemies if e['type'] == 'soldier')
    drone_count = sum(1 for e in enemies if e['type'] == 'drone')
    avg_speed = np.mean([e['speed'] for e in enemies])
    
    stats_text = f'总敌人数: {len(enemies)}\n士兵: {soldier_count} | 坦克: {drone_count}\n平均速度: {avg_speed:.1f}m/s'
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
           fontsize=10, va='top', ha='left',
           bbox=dict(boxstyle='round,pad=0.5', 
           facecolor='lightyellow', edgecolor='gray', alpha=0.9))
    
    # 保存图片
    plt.tight_layout()
    plt.savefig(filename, dpi=100, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    plt.close()
    
    print(f"✓ 已生成: {filename}")


def generate_type1_images(output_dir, count=10):
    """
    生成类型1图片：3个敌人，正常速度
    
    Args:
        output_dir: 输出目录
        count: 生成数量
    
    Returns:
        list: 图片数据列表
    """
    print("\n" + "="*60)
    print("生成类型1图片：少量敌人（3个），正常速度")
    print("="*60)
    
    image_data_list = []
    
    for i in range(1, count + 1):
        enemies = []
        for _ in range(3):
            enemy = generate_enemy(COORD_RANGE, SPEED_NORMAL)
            enemies.append(enemy)
        
        filename = os.path.join(output_dir, f'type1_sparse_{i:02d}.png')
        title = f'类型1 - 少量敌人 (图片 {i}/{count})'
        draw_battlefield(enemies, filename, title)
        
        # 保存图片数据
        image_data = {
            'imageId': f'type1_{i:02d}',
            'filename': f'type1_sparse_{i:02d}.png',
            'type': 'Type1_Sparse',
            'enemyCount': len(enemies),
            'speedRange': {'min': SPEED_NORMAL[0], 'max': SPEED_NORMAL[1]},
            'enemies': enemies
        }
        image_data_list.append(image_data)
    
    return image_data_list


def generate_type2_images(output_dir, count=10):
    """
    生成类型2图片：30个敌人，正常速度
    
    Args:
        output_dir: 输出目录
        count: 生成数量
    
    Returns:
        list: 图片数据列表
    """
    print("\n" + "="*60)
    print("生成类型2图片：密集敌人（30个），正常速度")
    print("="*60)
    
    image_data_list = []
    
    for i in range(1, count + 1):
        enemies = []
        for _ in range(30):
            enemy = generate_enemy(COORD_RANGE, SPEED_NORMAL)
            enemies.append(enemy)
        
        filename = os.path.join(output_dir, f'type2_dense_{i:02d}.png')
        title = f'类型2 - 密集敌人 (图片 {i}/{count})'
        draw_battlefield(enemies, filename, title)
        
        # 保存图片数据
        image_data = {
            'imageId': f'type2_{i:02d}',
            'filename': f'type2_dense_{i:02d}.png',
            'type': 'Type2_Dense',
            'enemyCount': len(enemies),
            'speedRange': {'min': SPEED_NORMAL[0], 'max': SPEED_NORMAL[1]},
            'enemies': enemies
        }
        image_data_list.append(image_data)
    
    return image_data_list


def generate_type3_images(output_dir, count=10):
    """
    生成类型3图片：30个敌人，快速移动
    
    Args:
        output_dir: 输出目录
        count: 生成数量
    
    Returns:
        list: 图片数据列表
    """
    print("\n" + "="*60)
    print("生成类型3图片：快速移动敌人（30个），高速")
    print("="*60)
    
    image_data_list = []
    
    for i in range(1, count + 1):
        enemies = []
        for _ in range(30):
            enemy = generate_enemy(COORD_RANGE, SPEED_FAST)
            enemies.append(enemy)
        
        filename = os.path.join(output_dir, f'type3_fast_{i:02d}.png')
        title = f'类型3 - 快速移动敌人 (图片 {i}/{count})'
        draw_battlefield(enemies, filename, title)
        
        # 保存图片数据
        image_data = {
            'imageId': f'type3_{i:02d}',
            'filename': f'type3_fast_{i:02d}.png',
            'type': 'Type3_Fast',
            'enemyCount': len(enemies),
            'speedRange': {'min': SPEED_FAST[0], 'max': SPEED_FAST[1]},
            'enemies': enemies
        }
        image_data_list.append(image_data)
    
    return image_data_list


def save_data_to_json(all_data, output_dir):
    """
    将所有图片数据保存为JSON文件
    
    Args:
        all_data: 所有图片数据
        output_dir: 输出目录
    """
    json_file = os.path.join(output_dir, 'battlefield_data.json')
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ 数据文件已保存: {json_file}")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("战场形态图生成器")
    print("="*60)
    print(f"图片尺寸: {IMAGE_SIZE}x{IMAGE_SIZE}像素")
    print(f"坐标范围: ±{COORD_RANGE}米")
    print(f"同心圆半径: {CIRCLE_RADII}米")
    print(f"正常速度范围: {SPEED_NORMAL[0]}-{SPEED_NORMAL[1]}米/秒")
    print(f"快速速度范围: {SPEED_FAST[0]}-{SPEED_FAST[1]}米/秒")
    
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = script_dir
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成三种类型的图片并收集数据
    type1_data = generate_type1_images(output_dir, count=10)
    type2_data = generate_type2_images(output_dir, count=10)
    type3_data = generate_type3_images(output_dir, count=10)
    
    # 汇总所有数据
    all_data = {
        'metadata': {
            'version': '1.0',
            'generatedAt': None,  # 可以添加时间戳
            'imageSize': IMAGE_SIZE,
            'coordinateRange': COORD_RANGE,
            'circleRadii': CIRCLE_RADII,
            'speedRanges': {
                'normal': {'min': SPEED_NORMAL[0], 'max': SPEED_NORMAL[1]},
                'fast': {'min': SPEED_FAST[0], 'max': SPEED_FAST[1]}
            },
            'totalImages': 30
        },
        'images': type1_data + type2_data + type3_data
    }
    
    # 保存JSON数据文件
    save_data_to_json(all_data, output_dir)
    
    print("\n" + "="*60)
    print("✅ 所有图片和数据生成完成！")
    print(f"总计生成: 30张图片 + 1个JSON数据文件")
    print(f"保存位置: {output_dir}")
    print("="*60)
    
    # 列出生成的文件
    print("\n生成的图片文件:")
    files = sorted([f for f in os.listdir(output_dir) if f.endswith('.png')])
    for f in files:
        print(f"  - {f}")
    
    print("\n数据文件:")
    print("  - battlefield_data.json")


if __name__ == "__main__":
    main()

