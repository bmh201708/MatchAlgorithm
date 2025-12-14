"""方向计算和马达映射模块"""
import math
import logging
from models import Position

logger = logging.getLogger(__name__)

# 马达方向描述（从玩家视角）
MOTOR_DIRECTIONS = {
    0: "正前方 (0°)",
    1: "前右 (45°)",
    2: "正右 (90°)",
    3: "后右 (135°)",
    4: "正后 (180°)",
    5: "后左 (225°)",
    6: "正左 (270°)",
    7: "前左 (315°)"
}


def calculate_direction_angle(player_pos: Position, target_pos: Position) -> float:
    """
    计算目标相对于玩家的水平方向角度
    
    坐标系：
    - X轴正方向：右
    - Y轴正方向：上
    - Z轴正方向：前
    
    Args:
        player_pos: 玩家位置
        target_pos: 目标位置
    
    Returns:
        角度（0-360度），0度为正前方（Z+），顺时针递增
    """
    # 计算从玩家到目标的向量（忽略Y轴，只考虑水平面）
    dx = target_pos.x - player_pos.x  # 右方向分量
    dz = target_pos.z - player_pos.z  # 前方向分量
    
    # 使用atan2计算角度（返回弧度，范围-π到π）
    # atan2(x, z): x为右（X轴），z为前（Z轴）
    # 结果：0度为正前方，顺时针为正
    angle_rad = math.atan2(dx, dz)
    
    # 转换为度数
    angle_deg = math.degrees(angle_rad)
    
    # 转换为0-360度范围
    if angle_deg < 0:
        angle_deg += 360
    
    logger.debug(f"Direction calculation: dx={dx:.2f}, dz={dz:.2f}, angle={angle_deg:.2f}°")
    
    return angle_deg


def angle_to_motor_id(angle: float) -> int:
    """
    将角度映射到马达编号（0-7）
    
    马达布局（俯视图，顺时针）：
    - 0号：0° ±22.5°（正前方）
    - 1号：45° ±22.5°（前右）
    - 2号：90° ±22.5°（正右）
    - 3号：135° ±22.5°（后右）
    - 4号：180° ±22.5°（正后）
    - 5号：225° ±22.5°（后左）
    - 6号：270° ±22.5°（正左）
    - 7号：315° ±22.5°（前左）
    
    Args:
        angle: 角度（0-360度）
    
    Returns:
        马达编号（0-7）
    """
    # 每个马达覆盖45度
    # round会将角度四舍五入到最近的45度倍数
    motor_id = round(angle / 45.0) % 8
    
    logger.debug(f"Angle {angle:.2f}° mapped to motor {motor_id}")
    
    return motor_id


def get_motor_direction_description(motor_id: int) -> str:
    """
    获取马达方向的文字描述
    
    Args:
        motor_id: 马达编号（0-7）
    
    Returns:
        方向描述字符串
    """
    return MOTOR_DIRECTIONS.get(motor_id, f"未知方向 (马达{motor_id})")


def calculate_motor_for_target(player_pos: Position, target_pos: Position) -> tuple:
    """
    计算目标对应的马达编号和详细信息
    
    Args:
        player_pos: 玩家位置
        target_pos: 目标位置
    
    Returns:
        元组 (motor_id, angle, direction_description)
    """
    angle = calculate_direction_angle(player_pos, target_pos)
    motor_id = angle_to_motor_id(angle)
    direction_desc = get_motor_direction_description(motor_id)
    
    logger.info(
        f"Target direction analysis: angle={angle:.2f}°, "
        f"motor_id={motor_id}, direction={direction_desc}"
    )
    
    return motor_id, angle, direction_desc


