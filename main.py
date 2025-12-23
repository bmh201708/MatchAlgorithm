"""主程序入口"""
import logging
import signal
import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入配置
from config import (
    LOG_LEVEL,
    LOG_FORMAT,
    LOG_DATE_FORMAT,
    SERIAL_PORT,
    SERIAL_BAUDRATE,
    NUM_VIBRATORS,
    UDP_HOST,
    UDP_PORT,
    VIBRATION_INTENSITY,
    VIBRATION_DURATION,
    VIBRATION_MODE_DRONE,
    VIBRATION_MODE_SOLDIER,
    ENABLE_IFS_ASSESSMENT,
    ENABLE_GPT_ASSESSMENT,
    ENABLE_TERRAIN_ANALYSIS,
    THREAT_ASSESSMENT_STRATEGY
)

from threat_analyzer import find_most_threatening_target
from serial_handler import SerialHandler
from udp_server import UDPServer
from direction_mapper import calculate_motor_for_target
from situation_awareness import (
    calculate_all_directions_threat,
    normalize_threat_to_intensity
)
from csv_logger import CSVLogger

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT
)

logger = logging.getLogger(__name__)

# 全局变量，用于优雅退出
running = True


def signal_handler(sig, frame):
    """处理中断信号（Ctrl+C）"""
    global running
    logger.info("Received interrupt signal, shutting down...")
    running = False


def main():
    """主函数"""
    global running
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 打印系统配置信息
    print("\n" + "=" * 70)
    print("🎯 威胁感知触觉反馈系统 - 启动配置")
    print("=" * 70)
    print(f"威胁评估策略: {THREAT_ASSESSMENT_STRATEGY}")
    print(f"  - IFS评估: {'✓ 已启用' if ENABLE_IFS_ASSESSMENT else '✗ 已禁用'}")
    print(f"  - GPT评估: {'✓ 已启用' if ENABLE_GPT_ASSESSMENT else '✗ 已禁用'}")
    print(f"  - 地形分析: {'✓ 已启用' if ENABLE_TERRAIN_ANALYSIS else '✗ 已禁用'}")
    print(f"串口配置: {SERIAL_PORT} @ {SERIAL_BAUDRATE} bps")
    print(f"UDP配置: {UDP_HOST}:{UDP_PORT}")
    print("=" * 70 + "\n")
    
    # 初始化UDP服务器
    udp_server = UDPServer(host=UDP_HOST, port=UDP_PORT)
    if not udp_server.start():
        logger.error("Failed to start UDP server, exiting...")
        sys.exit(1)
    
    # 初始化串口处理器
    serial_handler = SerialHandler(port=SERIAL_PORT, baudrate=SERIAL_BAUDRATE)
    if not serial_handler.connect():
        logger.error("Failed to connect to serial port, exiting...")
        udp_server.stop()
        sys.exit(1)
    
    # 询问用户是否进行硬件测试
    print("\n" + "=" * 60)
    print("🔧 硬件测试选项")
    print("=" * 60)
    user_input = input("是否进行硬件测试？(Y/N): ").strip().upper()
    
    if user_input == 'Y':
        logger.info("User chose to perform hardware test")
        if not serial_handler.hardware_test(num_vibrators=NUM_VIBRATORS, test_duration=1.0):
            logger.warning("Hardware test failed, but continuing with main program...")
    else:
        logger.info("User skipped hardware test")
    
    # 初始化CSV日志记录器
    csv_logger = None
    try:
        csv_logger = CSVLogger(base_dir="logs")
    except Exception as e:
        logger.error(f"Failed to initialize CSV logger: {e}")
        logger.warning("Continuing without CSV logging...")
    
    # 工作模式说明
    print("\n" + "=" * 60)
    print("🎮 工作模式：单目标模式（默认）")
    print("=" * 60)
    print("• 默认：单目标模式 - 震动威胁最大的单个敌人方向")
    print("• 特殊信号：收到Unity信号时临时切换到态势感知模式（3秒）")
    print("=" * 60)
    logger.info("Default mode: Single Target Mode")
    logger.info("System initialized successfully. Waiting for data...")
    
    try:
        while running:
            # 接收UDP数据
            game_data = udp_server.receive_data()
            
            if game_data is None:
                # 超时或接收失败，继续循环
                continue
            
            # 打印接收到的数据详情
            logger.info("=" * 60)
            logger.info(f"Processing received data - Round: {game_data.round}")
            logger.info(f"Player Position: X={game_data.playerPosition.x:.2f}, Y={game_data.playerPosition.y:.2f}, Z={game_data.playerPosition.z:.2f}")
            logger.info(f"Total targets: {len(game_data.targets)}")
            for i, target in enumerate(game_data.targets, 1):
                velocity_info = f", Velocity={target.velocity:.2f} m/s" if target.velocity is not None else ""
                direction_info = f", Direction={target.direction:.2f}°" if target.direction is not None else ""
                logger.info(
                    f"  Target {i}: ID={target.id}, Type={target.type}, "
                    f"Distance={target.distance:.2f}, Angle={target.angle:.2f}°, "
                    f"Position=({target.position.x:.2f}, {target.position.y:.2f}, {target.position.z:.2f})"
                    f"{velocity_info}{direction_info}"
                )
            logger.info("=" * 60)
            
            # 如果没有目标，跳过
            if not game_data.targets:
                logger.warning("No targets in received data, skipping...")
                continue
            
            # ========== 步骤1：检查round是否已存在 ==========
            round_exists = csv_logger.check_round_exists(game_data.round) if csv_logger else False
            
            if not round_exists:
                # ========== 步骤2：计算威胁数据 ==========
                logger.info(f"📝 Round {game_data.round} is new, calculating threat data...")
                most_threatening = find_most_threatening_target(game_data)
                direction_threats = calculate_all_directions_threat(game_data)
                
                # ========== 步骤3：写入CSV ==========
                if csv_logger:
                    csv_logger.log_round_data(
                        round_number=game_data.round,
                        most_threatening_target=most_threatening,
                        direction_threats=direction_threats
                    )
                    logger.info(f"✓ Round {game_data.round} data saved to CSV")
            else:
                logger.info(f"📋 Round {game_data.round} already exists in CSV, skipping calculation")
            
            # ========== 步骤4：从CSV读取数据 ==========
            round_data = csv_logger.read_round_data(game_data.round) if csv_logger else None
            
            if not round_data:
                logger.error(f"Failed to read round {game_data.round} data from CSV, skipping vibration")
                continue
            
            # 计算敌人方向对应的马达编号
            motor_id, direction_angle, direction_desc = calculate_motor_for_target(
                game_data.playerPosition,
                most_threatening.position
            )
            
            # 根据敌人类型选择震动模式
            # Drone: 模式0 (持续震动)
            # Soldier: 模式1 (超快脉冲)
            is_drone = most_threatening.type.lower() == "drone"
            vibration_mode = VIBRATION_MODE_DRONE if is_drone else VIBRATION_MODE_SOLDIER
            mode_name = "持续震动" if vibration_mode == VIBRATION_MODE_DRONE else "超快脉冲"
            
            # 使用配置的震动参数
            intensity = VIBRATION_INTENSITY
            duration = VIBRATION_DURATION
            
            # 打印方向分析结果
            logger.info("─" * 60)
            logger.info("🎯 Threat Direction Analysis")
            logger.info(f"  Most threatening target: ID={most_threatening.id}, Type={most_threatening.type}")
            logger.info(f"  Target position: ({most_threatening.position.x:.2f}, {most_threatening.position.y:.2f}, {most_threatening.position.z:.2f})")
            logger.info(f"  Direction angle: {direction_angle:.2f}°")
            logger.info(f"  Selected motor: #{motor_id} - {direction_desc}")
            logger.info(f"  Vibration intensity: {intensity} (HIGH)")
            logger.info(f"  Vibration mode: {vibration_mode} ({mode_name})")
            logger.info(f"  Duration: {duration}s")
            logger.info("─" * 60)
            
            # 发送震动信号
            success = serial_handler.send_vibration(motor_id, intensity, duration, vibration_mode)
            
            if not success:
                logger.error("Failed to send vibration signal")
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
    finally:
        # 清理资源
        logger.info("Cleaning up resources...")
        if csv_logger:
            csv_logger.close()
        serial_handler.disconnect()
        udp_server.stop()
        logger.info("System shutdown complete")


if __name__ == "__main__":
    main()

