using System;
using System.Collections.Generic;
using System.IO;
using Newtonsoft.Json;  // 需要安装 Newtonsoft.Json NuGet包

namespace BattlefieldDataReader
{
    /// <summary>
    /// 战场数据读取示例 - C#版本
    /// 用于读取Python生成的battlefield_data.json文件
    /// </summary>
    
    // 数据模型类
    public class BattlefieldData
    {
        [JsonProperty("metadata")]
        public Metadata Metadata { get; set; }
        
        [JsonProperty("images")]
        public List<ImageData> Images { get; set; }
    }
    
    public class Metadata
    {
        [JsonProperty("version")]
        public string Version { get; set; }
        
        [JsonProperty("generatedAt")]
        public DateTime? GeneratedAt { get; set; }
        
        [JsonProperty("imageSize")]
        public int ImageSize { get; set; }
        
        [JsonProperty("coordinateRange")]
        public int CoordinateRange { get; set; }
        
        [JsonProperty("circleRadii")]
        public List<int> CircleRadii { get; set; }
        
        [JsonProperty("speedRanges")]
        public SpeedRanges SpeedRanges { get; set; }
        
        [JsonProperty("totalImages")]
        public int TotalImages { get; set; }
    }
    
    public class SpeedRanges
    {
        [JsonProperty("normal")]
        public SpeedRange Normal { get; set; }
        
        [JsonProperty("fast")]
        public SpeedRange Fast { get; set; }
    }
    
    public class SpeedRange
    {
        [JsonProperty("min")]
        public int Min { get; set; }
        
        [JsonProperty("max")]
        public int Max { get; set; }
    }
    
    public class ImageData
    {
        [JsonProperty("imageId")]
        public string ImageId { get; set; }
        
        [JsonProperty("filename")]
        public string Filename { get; set; }
        
        [JsonProperty("type")]
        public string Type { get; set; }
        
        [JsonProperty("enemyCount")]
        public int EnemyCount { get; set; }
        
        [JsonProperty("speedRange")]
        public SpeedRange SpeedRange { get; set; }
        
        [JsonProperty("enemies")]
        public List<Enemy> Enemies { get; set; }
    }
    
    public class Enemy
    {
        [JsonProperty("type")]
        public string Type { get; set; }  // "soldier" 或 "tank"
        
        [JsonProperty("x")]
        public double X { get; set; }
        
        [JsonProperty("y")]
        public double Y { get; set; }
        
        [JsonProperty("speed")]
        public double Speed { get; set; }
        
        [JsonProperty("direction")]
        public double Direction { get; set; }  // 0-360度
        
        // 辅助属性
        public bool IsTank => Type == "tank";
        public bool IsSoldier => Type == "soldier";
    }
    
    // 读取和使用示例
    public class Program
    {
        public static void Main(string[] args)
        {
            // 读取JSON文件
            string jsonFilePath = "battlefield_data.json";
            
            try
            {
                // 读取JSON文件内容
                string jsonContent = File.ReadAllText(jsonFilePath);
                
                // 反序列化为C#对象
                BattlefieldData battlefieldData = JsonConvert.DeserializeObject<BattlefieldData>(jsonContent);
                
                // 输出元数据信息
                Console.WriteLine("=== 战场数据概览 ===");
                Console.WriteLine($"版本: {battlefieldData.Metadata.Version}");
                Console.WriteLine($"图片尺寸: {battlefieldData.Metadata.ImageSize}x{battlefieldData.Metadata.ImageSize}");
                Console.WriteLine($"坐标范围: ±{battlefieldData.Metadata.CoordinateRange}米");
                Console.WriteLine($"总图片数: {battlefieldData.Metadata.TotalImages}");
                Console.WriteLine();
                
                // 遍历所有图片
                foreach (var image in battlefieldData.Images)
                {
                    Console.WriteLine($"--- {image.ImageId} ({image.Filename}) ---");
                    Console.WriteLine($"类型: {image.Type}");
                    Console.WriteLine($"敌人总数: {image.EnemyCount}");
                    
                    // 统计士兵和坦克数量
                    int soldierCount = 0;
                    int tankCount = 0;
                    
                    foreach (var enemy in image.Enemies)
                    {
                        if (enemy.IsSoldier)
                            soldierCount++;
                        else if (enemy.IsTank)
                            tankCount++;
                    }
                    
                    Console.WriteLine($"士兵: {soldierCount}, 坦克: {tankCount}");
                    Console.WriteLine();
                }
                
                // 示例：获取第一张图片的数据
                Console.WriteLine("=== 示例：读取第一张图片的敌人详情 ===");
                var firstImage = battlefieldData.Images[0];
                Console.WriteLine($"图片: {firstImage.Filename}");
                
                for (int i = 0; i < firstImage.Enemies.Count; i++)
                {
                    var enemy = firstImage.Enemies[i];
                    Console.WriteLine($"敌人 {i + 1}:");
                    Console.WriteLine($"  类型: {(enemy.IsTank ? "坦克" : "士兵")}");
                    Console.WriteLine($"  坐标: ({enemy.X:F2}, {enemy.Y:F2})米");
                    Console.WriteLine($"  速度: {enemy.Speed:F2}米/秒");
                    Console.WriteLine($"  方向: {enemy.Direction:F2}度");
                }
                
                // 示例：筛选特定类型的图片
                Console.WriteLine("\n=== 示例：筛选类型3图片 ===");
                var type3Images = battlefieldData.Images.FindAll(img => img.Type == "Type3_Fast");
                Console.WriteLine($"找到 {type3Images.Count} 张类型3图片");
                
                // 示例：查找所有坦克
                Console.WriteLine("\n=== 示例：统计所有坦克 ===");
                int totalTanks = 0;
                foreach (var image in battlefieldData.Images)
                {
                    totalTanks += image.Enemies.FindAll(e => e.IsTank).Count;
                }
                Console.WriteLine($"所有图片中共有 {totalTanks} 个坦克");
                
            }
            catch (FileNotFoundException)
            {
                Console.WriteLine($"错误: 找不到文件 '{jsonFilePath}'");
            }
            catch (JsonException ex)
            {
                Console.WriteLine($"JSON解析错误: {ex.Message}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"发生错误: {ex.Message}");
            }
        }
    }
}

