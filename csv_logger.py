"""CSV日志记录模块"""
import csv
import logging
import os
from datetime import datetime
from typing import Optional, List
from models import Target

logger = logging.getLogger(__name__)


class CSVLogger:
    """CSV日志记录器，用于记录实验数据"""
    
    def __init__(self, base_dir: str = "logs"):
        """
        初始化CSV日志记录器
        
        Args:
            base_dir: 日志文件存储目录，默认为 "logs"
        """
        self.base_dir = base_dir
        self.csv_file = None
        self.csv_writer = None
        self.file_path = None
        
        # 创建日志目录
        self._create_log_directory()
        
        # 创建CSV文件
        self._create_csv_file()
    
    def _create_log_directory(self):
        """创建日志目录（如果不存在）"""
        try:
            if not os.path.exists(self.base_dir):
                os.makedirs(self.base_dir)
                logger.info(f"Created log directory: {self.base_dir}")
        except Exception as e:
            logger.error(f"Failed to create log directory: {e}")
            raise
    
    def _create_csv_file(self):
        """创建带时间戳的CSV文件并写入列头"""
        try:
            # 生成文件名（使用时间戳）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.file_path = os.path.join(self.base_dir, f"experiment_{timestamp}.csv")
            
            # 打开文件
            self.csv_file = open(self.file_path, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.csv_file)
            
            # 写入列头
            headers = [
                'timestamp',
                'round',
                'threat_enemy_id',
                'threat_enemy_type',
                'threat_enemy_distance',
                'threat_enemy_angle',
                'threat_enemy_x',
                'threat_enemy_y',
                'threat_enemy_z',
                'north_threat',
                'northeast_threat',
                'east_threat',
                'southeast_threat',
                'south_threat',
                'southwest_threat',
                'west_threat',
                'northwest_threat'
            ]
            self.csv_writer.writerow(headers)
            self.csv_file.flush()
            
            logger.info("=" * 60)
            logger.info("📊 CSV Logger initialized")
            logger.info(f"  File path: {self.file_path}")
            logger.info(f"  Columns: {len(headers)}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Failed to create CSV file: {e}")
            raise
    
    def log_round_data(
        self,
        round_number: str,
        most_threatening_target: Optional[Target],
        direction_threats: List[float]
    ):
        """
        记录每轮的数据到CSV
        
        Args:
            round_number: 轮次编号（如 "1-1"）
            most_threatening_target: 最具威胁的目标对象，如果没有则为None
            direction_threats: 8个方向的威胁值列表 [北, 东北, 东, 东南, 南, 西南, 西, 西北]
        """
        if not self.csv_writer or not self.csv_file:
            logger.error("CSV logger is not initialized")
            return
        
        try:
            # 生成时间戳（精确到毫秒）
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            # 提取威胁目标信息
            if most_threatening_target:
                threat_id = most_threatening_target.id
                threat_type = most_threatening_target.type
                threat_distance = round(most_threatening_target.distance, 2)
                threat_angle = round(most_threatening_target.angle, 2)
                threat_x = round(most_threatening_target.position.x, 2)
                threat_y = round(most_threatening_target.position.y, 2)
                threat_z = round(most_threatening_target.position.z, 2)
            else:
                threat_id = "N/A"
                threat_type = "N/A"
                threat_distance = "N/A"
                threat_angle = "N/A"
                threat_x = "N/A"
                threat_y = "N/A"
                threat_z = "N/A"
            
            # 确保有8个方向的威胁值
            if len(direction_threats) != 8:
                logger.warning(f"Expected 8 direction threats, got {len(direction_threats)}")
                direction_threats = direction_threats + [0.0] * (8 - len(direction_threats))
            
            # 四舍五入威胁值到3位小数
            direction_threats_rounded = [round(t, 3) for t in direction_threats[:8]]
            
            # 写入数据行
            row = [
                timestamp,
                round_number,
                threat_id,
                threat_type,
                threat_distance,
                threat_angle,
                threat_x,
                threat_y,
                threat_z,
            ] + direction_threats_rounded
            
            self.csv_writer.writerow(row)
            self.csv_file.flush()  # 立即写入磁盘
            
            logger.debug(f"CSV: Logged data for round {round_number}")
            
        except Exception as e:
            logger.error(f"Failed to write to CSV file: {e}")
            # 不抛出异常，避免中断主程序
    
    def close(self):
        """关闭CSV文件"""
        if self.csv_file:
            try:
                self.csv_file.close()
                logger.info(f"CSV log file closed: {self.file_path}")
            except Exception as e:
                logger.error(f"Error closing CSV file: {e}")
    
    def __enter__(self):
        """支持with语句"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持with语句"""
        self.close()
        return False

