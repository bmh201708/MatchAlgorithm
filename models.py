"""数据模型定义模块"""
from dataclasses import dataclass, field
from typing import List, Optional
import math


@dataclass
class Position:
    """位置坐标"""
    x: float
    y: float
    z: float


@dataclass
class Target:
    """敌人目标信息"""
    id: int
    angle: float
    distance: float
    type: str  # "Tank" or "Soldier"
    position: Position
    velocity: Optional[float] = None  # 速度（米/秒），可选
    direction: Optional[float] = None  # 移动方向（度，0-360），可选


@dataclass
class GameData:
    """游戏数据"""
    round: int
    playerPosition: Position
    targets: List[Target]
    situationAwareness: bool = False  # 是否启用态势感知模式

    @classmethod
    def from_dict(cls, data: dict) -> 'GameData':
        """从字典创建GameData对象，支持两种数据格式"""
        player_pos = Position(**data['playerPosition'])
        targets = []
        
        # 检查是使用 'targets' 还是 'enemies' 字段
        if 'targets' in data:
            # 原有格式：包含 angle, distance, position 等字段
            for target_data in data['targets']:
                target_pos = Position(**target_data['position'])
                target = Target(
                    id=target_data['id'],
                    angle=target_data['angle'],
                    distance=target_data['distance'],
                    type=target_data['type'],
                    position=target_pos,
                    velocity=target_data.get('velocity') or target_data.get('speed'),
                    direction=target_data.get('direction')
                )
                targets.append(target)
        elif 'enemies' in data:
            # 新格式：包含 x, z 坐标，需要计算 angle 和 distance
            for enemy_data in data['enemies']:
                # 构建敌人位置（使用 x, z，y 默认为玩家高度）
                enemy_x = enemy_data['x']
                enemy_z = enemy_data['z']
                enemy_pos = Position(x=enemy_x, y=player_pos.y, z=enemy_z)
                
                # 计算相对位置
                dx = enemy_x - player_pos.x
                dz = enemy_z - player_pos.z
                
                # 计算距离
                distance = math.sqrt(dx * dx + dz * dz)
                
                # 计算角度（从北方向顺时针，0-360度）
                # math.atan2 返回 -π 到 π，需要转换为 0-360
                angle_rad = math.atan2(dx, dz)  # 注意：x对应sin，z对应cos
                angle = math.degrees(angle_rad)
                if angle < 0:
                    angle += 360
                
                target = Target(
                    id=enemy_data['id'],
                    angle=angle,
                    distance=distance,
                    type=enemy_data['type'],
                    position=enemy_pos,
                    velocity=enemy_data.get('velocity') or enemy_data.get('speed'),
                    direction=enemy_data.get('direction')
                )
                targets.append(target)
        else:
            raise KeyError("'targets' or 'enemies'")
        
        # 检查是否启用态势感知模式（支持多种字段名）
        situation_awareness = data.get('situationAwareness', False) or data.get('enableSituationAwareness', False)
        
        return cls(
            round=data['round'],
            playerPosition=player_pos,
            targets=targets,
            situationAwareness=situation_awareness
        )

