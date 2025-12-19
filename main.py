"""主程序入口"""
import logging
import signal
import sys
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
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
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
    
    # 初始化UDP服务器
    udp_server = UDPServer(host="0.0.0.0", port=5005)
    if not udp_server.start():
        logger.error("Failed to start UDP server, exiting...")
        sys.exit(1)
    
    # 初始化串口处理器
    serial_handler = SerialHandler(port="COM7", baudrate=9600)
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
        if not serial_handler.hardware_test(num_vibrators=8, test_duration=1.0):
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
            
            # 检查是否收到态势感知信号
            if game_data.situationAwareness:
                # ========== 态势感知模式（临时触发，3秒后自动结束）==========
                logger.info("🌐 收到态势感知信号，临时切换到态势感知模式（3秒）")
                
                # 计算所有方向的威胁度
                direction_threats = calculate_all_directions_threat(game_data)
                
                # 找出最具威胁的目标（用于CSV记录）
                most_threatening = find_most_threatening_target(game_data)
                
                # 记录到CSV
                if csv_logger:
                    csv_logger.log_round_data(
                        round_number=game_data.round,
                        most_threatening_target=most_threatening,
                        direction_threats=direction_threats
                    )
                
                # 将威胁度映射到震动强度
                intensities = normalize_threat_to_intensity(
                    direction_threats,
                    min_intensity=0,
                    max_intensity=255,
                    threshold=0.01
                )
                
                # 使用持续震动模式（模式0），持续3秒
                vibration_mode = 0
                duration = 3.0
                
                # 发送多马达震动信号
                success = serial_handler.send_multi_vibration(
                    intensities,
                    duration=duration,
                    mode=vibration_mode
                )
                
                if not success:
                    logger.error("Failed to send multi-motor vibration signals")
                else:
                    logger.info("✓ 态势感知震动已发送，将持续3秒后自动结束")
                    logger.info("─" * 60)
            else:
                # ========== 单目标模式（原有逻辑）==========
                # 找出最有威胁的目标
                most_threatening = find_most_threatening_target(game_data)
                
                if most_threatening is None:
                    logger.warning("Could not determine most threatening target")
                    continue
                
                # 计算所有方向的威胁度（用于CSV记录）
                direction_threats = calculate_all_directions_threat(game_data)
                
                # 记录到CSV
                if csv_logger:
                    csv_logger.log_round_data(
                        round_number=game_data.round,
                        most_threatening_target=most_threatening,
                        direction_threats=direction_threats
                    )
                
                # 计算敌人方向对应的马达编号
                motor_id, direction_angle, direction_desc = calculate_motor_for_target(
                    game_data.playerPosition,
                    most_threatening.position
                )
                
                # 获取目标距离
                target_distance = most_threatening.distance
                
                # 第一阶段：根据目标类别选择震动模式
                # IFV: 模式0, Soldier: 模式2
                if most_threatening.type.lower() == "ifv":
                    type_mode = 0
                    type_mode_name = "持续震动"
                elif most_threatening.type.lower() == "soldier":
                    type_mode = 2
                    type_mode_name = "模式2"
                else:
                    # 其他类型默认使用模式0
                    type_mode = 0
                    type_mode_name = "持续震动(默认)"
                
                # 第二阶段：根据目标距离选择震动模式
                # <10m: 模式0, 10-20m: 模式2, >20m: 模式3
                if target_distance < 10:
                    distance_mode = 0
                    distance_mode_name = "持续震动 (<10m)"
                elif target_distance <= 20:
                    distance_mode = 2
                    distance_mode_name = "模式2 (10-20m)"
                else:
                    distance_mode = 3
                    distance_mode_name = "模式3 (>20m)"
                
                # 固定使用最高强度和3秒持续时间
                intensity = 255
                duration = 3.0
                
                # 打印威胁分析结果
                logger.info("─" * 60)
                logger.info("🎯 单目标模式 - 两阶段震动")
                logger.info(f"  最具威胁目标: ID={most_threatening.id}, Type={most_threatening.type}")
                logger.info(f"  目标位置: ({most_threatening.position.x:.2f}, {most_threatening.position.y:.2f}, {most_threatening.position.z:.2f})")
                logger.info(f"  目标距离: {target_distance:.2f}m")
                logger.info(f"  方向角度: {direction_angle:.2f}°")
                logger.info(f"  选择马达: #{motor_id} - {direction_desc}")
                logger.info(f"  震动强度: {intensity}")
                logger.info(f"  第一阶段(类别): 模式{type_mode} ({type_mode_name}), 持续{duration}s")
                logger.info(f"  第二阶段(距离): 模式{distance_mode} ({distance_mode_name}), 持续{duration}s")
                logger.info("─" * 60)
                
                # 第一阶段：震动目标类别
                import time
                logger.info(f"▶ 第一阶段：震动目标类别 - 模式{type_mode}")
                success1 = serial_handler.send_vibration(motor_id, intensity, duration, type_mode)
                if not success1:
                    logger.error("第一阶段震动发送失败")
                
                # 等待第一阶段震动完成并间隔2秒
                time.sleep(duration + 2.0)
                logger.info("⏸ 间隔2秒完成")
                
                # 第二阶段：震动目标距离
                logger.info(f"▶ 第二阶段：震动目标距离 - 模式{distance_mode}")
                success2 = serial_handler.send_vibration(motor_id, intensity, duration, distance_mode)
                if not success2:
                    logger.error("第二阶段震动发送失败")
                
                logger.info("✓ 两阶段震动完成")
                logger.info("─" * 60)
    
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

