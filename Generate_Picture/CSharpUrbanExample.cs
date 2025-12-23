using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json;  // 需要安装 Newtonsoft.Json NuGet包

namespace UrbanBattlefieldDataReader
{
    /// <summary>
    /// 巷道战场数据读取示例 - C#版本
    /// 用于读取Python生成的urban_battlefield_data.json文件
    /// </summary>
    
    #region 数据模型类
    
    // 根数据类
    public class UrbanBattlefieldData
    {
        [JsonProperty("metadata")]
        public Metadata Metadata { get; set; }
        
        [JsonProperty("terrain")]
        public TerrainData Terrain { get; set; }
        
        [JsonProperty("images")]
        public List<ImageData> Images { get; set; }
    }
    
    // 元数据
    public class Metadata
    {
        [JsonProperty("version")]
        public string Version { get; set; }
        
        [JsonProperty("generatedAt")]
        public string GeneratedAt { get; set; }
        
        [JsonProperty("terrainFile")]
        public string TerrainFile { get; set; }
        
        [JsonProperty("coordinateSystem")]
        public string CoordinateSystem { get; set; }
        
        [JsonProperty("imageSize")]
        public int ImageSize { get; set; }
        
        [JsonProperty("coordinateRange")]
        public int CoordinateRange { get; set; }
        
        [JsonProperty("circleRadii")]
        public List<int> CircleRadii { get; set; }
        
        [JsonProperty("tactics")]
        public List<string> Tactics { get; set; }
        
        [JsonProperty("totalImages")]
        public int TotalImages { get; set; }
    }
    
    // 地形数据
    public class TerrainData
    {
        [JsonProperty("buildings")]
        public List<Building> Buildings { get; set; }
        
        [JsonProperty("alleys")]
        public List<Alley> Alleys { get; set; }
        
        [JsonProperty("obstacles")]
        public List<Obstacle> Obstacles { get; set; }
    }
    
    // 建筑物
    public class Building
    {
        [JsonProperty("id")]
        public int Id { get; set; }
        
        [JsonProperty("x")]
        public double X { get; set; }
        
        [JsonProperty("z")]
        public double Z { get; set; }
        
        [JsonProperty("width")]
        public double Width { get; set; }
        
        [JsonProperty("depth")]
        public double Depth { get; set; }
        
        [JsonProperty("height")]
        public double Height { get; set; }
        
        [JsonProperty("walls")]
        public List<object> Walls { get; set; }
        
        [JsonProperty("doors")]
        public List<object> Doors { get; set; }
        
        [JsonProperty("windows")]
        public List<object> Windows { get; set; }
    }
    
    // 巷道
    public class Alley
    {
        [JsonProperty("id")]
        public int Id { get; set; }
        
        [JsonProperty("start_x")]
        public double StartX { get; set; }
        
        [JsonProperty("start_z")]
        public double StartZ { get; set; }
        
        [JsonProperty("end_x")]
        public double EndX { get; set; }
        
        [JsonProperty("end_z")]
        public double EndZ { get; set; }
        
        [JsonProperty("width")]
        public double Width { get; set; }
        
        [JsonProperty("length")]
        public double Length { get; set; }
    }
    
    // 障碍物
    public class Obstacle
    {
        [JsonProperty("id")]
        public int Id { get; set; }
        
        [JsonProperty("type")]
        public string Type { get; set; }  // "Cover", "Barrier", "Vehicle"
        
        [JsonProperty("x")]
        public double X { get; set; }
        
        [JsonProperty("z")]
        public double Z { get; set; }
        
        [JsonProperty("width")]
        public double Width { get; set; }
        
        [JsonProperty("depth")]
        public double Depth { get; set; }
        
        [JsonProperty("rotation")]
        public double Rotation { get; set; }
        
        // 辅助属性
        public bool IsCover => Type == "Cover";
        public bool IsBarrier => Type == "Barrier";
        public bool IsVehicle => Type == "Vehicle";
    }
    
    // 图片数据
    public class ImageData
    {
        [JsonProperty("imageId")]
        public string ImageId { get; set; }
        
        [JsonProperty("filename")]
        public string Filename { get; set; }
        
        [JsonProperty("type")]
        public string Type { get; set; }
        
        [JsonProperty("tacticType")]
        public string TacticType { get; set; }
        
        [JsonProperty("tacticNameCN")]
        public string TacticNameCN { get; set; }
        
        [JsonProperty("enemyCount")]
        public int EnemyCount { get; set; }
        
        [JsonProperty("speedRange")]
        public SpeedRange SpeedRange { get; set; }
        
        [JsonProperty("enemies")]
        public List<Enemy> Enemies { get; set; }
        
        // 辅助属性
        public bool IsType1 => Type.StartsWith("Type1");
        public bool IsType2 => Type.StartsWith("Type2");
        public bool IsType3 => Type.StartsWith("Type3");
    }
    
    // 速度范围
    public class SpeedRange
    {
        [JsonProperty("min")]
        public double Min { get; set; }
        
        [JsonProperty("max")]
        public double Max { get; set; }
    }
    
    // 敌人
    public class Enemy
    {
        [JsonProperty("id")]
        public int Id { get; set; }  // 敌人编号（从1开始）
        
        [JsonProperty("type")]
        public string Type { get; set; }  // "soldier" 或 "ifv" (无人机)
        
        [JsonProperty("x")]
        public double X { get; set; }
        
        [JsonProperty("z")]
        public double Z { get; set; }
        
        [JsonProperty("speed")]
        public double Speed { get; set; }
        
        [JsonProperty("direction")]
        public double Direction { get; set; }  // 0-360度
        
        // 辅助属性
        public bool IsDrone => Type == "ifv";  // 无人机
        public bool IsSoldier => Type == "soldier";
        
        // 计算距离（到原点）
        public double DistanceFromCenter => Math.Sqrt(X * X + Z * Z);
    }
    
    // 战术类型枚举
    public enum TacticType
    {
        Encirclement,       // 包围
        Pincer,             // 钳形攻势
        Ambush,             // 伏击
        Retreat,            // 撤退
        FrontalAssault,     // 正面突击
        Flanking,           // 侧翼包抄
        Defensive,          // 防御阵型
        Guerrilla,          // 游击骚扰
        Pursuit,            // 追击
        Dispersed           // 分散机动
    }
    
    #endregion
    
    // 主程序
    public class Program
    {
        public static void Main(string[] args)
        {
            // 读取JSON文件
            string jsonFilePath = "urban_battlefield_data.json";
            
            try
            {
                // 读取JSON文件内容
                string jsonContent = File.ReadAllText(jsonFilePath);
                
                // 反序列化为C#对象
                UrbanBattlefieldData battlefieldData = JsonConvert.DeserializeObject<UrbanBattlefieldData>(jsonContent);
                
                // ===== 输出元数据信息 =====
                Console.WriteLine("=== 巷道战场数据概览 ===");
                Console.WriteLine($"版本: {battlefieldData.Metadata.Version}");
                Console.WriteLine($"生成时间: {battlefieldData.Metadata.GeneratedAt}");
                Console.WriteLine($"地形文件: {battlefieldData.Metadata.TerrainFile}");
                Console.WriteLine($"坐标系统: {battlefieldData.Metadata.CoordinateSystem}");
                Console.WriteLine($"图片尺寸: {battlefieldData.Metadata.ImageSize}x{battlefieldData.Metadata.ImageSize}");
                Console.WriteLine($"坐标范围: ±{battlefieldData.Metadata.CoordinateRange}米");
                Console.WriteLine($"战术类型: {battlefieldData.Metadata.Tactics.Count}种");
                Console.WriteLine($"总图片数: {battlefieldData.Metadata.TotalImages}");
                Console.WriteLine();
                
                // ===== 输出地形信息 =====
                Console.WriteLine("=== 地形信息 ===");
                Console.WriteLine($"建筑物: {battlefieldData.Terrain.Buildings.Count}栋");
                Console.WriteLine($"巷道: {battlefieldData.Terrain.Alleys.Count}条");
                Console.WriteLine($"障碍物: {battlefieldData.Terrain.Obstacles.Count}个");
                
                // 统计障碍物类型
                int coverCount = battlefieldData.Terrain.Obstacles.Count(o => o.IsCover);
                int barrierCount = battlefieldData.Terrain.Obstacles.Count(o => o.IsBarrier);
                int vehicleCount = battlefieldData.Terrain.Obstacles.Count(o => o.IsVehicle);
                Console.WriteLine($"  - 掩体: {coverCount}个");
                Console.WriteLine($"  - 路障: {barrierCount}个");
                Console.WriteLine($"  - 车辆: {vehicleCount}个");
                Console.WriteLine();
                
                // ===== 遍历所有图片 =====
                Console.WriteLine("=== 图片列表 ===");
                var groupedImages = battlefieldData.Images.GroupBy(img => img.Type);
                
                foreach (var group in groupedImages)
                {
                    Console.WriteLine($"\n{group.Key}:");
                    foreach (var image in group)
                    {
                        Console.WriteLine($"  - {image.Filename}");
                        Console.WriteLine($"    战术: {image.TacticNameCN} ({image.TacticType})");
                        Console.WriteLine($"    敌人: {image.EnemyCount}个");
                        
                        // 统计士兵和无人机数量
                        int soldierCount = image.Enemies.Count(e => e.IsSoldier);
                        int ifvCount = image.Enemies.Count(e => e.IsDrone);
                        Console.WriteLine($"    士兵: {soldierCount}, 无人机: {ifvCount}");
                    }
                }
                
                // ===== 示例：读取第一张图片的敌人详情 =====
                Console.WriteLine("\n=== 示例：读取第一张图片的敌人详情 ===");
                var firstImage = battlefieldData.Images[0];
                Console.WriteLine($"图片: {firstImage.Filename}");
                Console.WriteLine($"战术: {firstImage.TacticNameCN}");
                Console.WriteLine($"敌人总数: {firstImage.EnemyCount}");
                
                for (int i = 0; i < Math.Min(5, firstImage.Enemies.Count); i++)
                {
                    var enemy = firstImage.Enemies[i];
                    Console.WriteLine($"\n敌人 #{enemy.Id}:");
                    Console.WriteLine($"  类型: {(enemy.IsDrone ? "无人机" : "士兵")}");
                    Console.WriteLine($"  坐标: ({enemy.X:F2}, {enemy.Z:F2})米");
                    Console.WriteLine($"  速度: {enemy.Speed:F2}米/秒");
                    Console.WriteLine($"  方向: {enemy.Direction:F2}度");
                    Console.WriteLine($"  距离: {enemy.DistanceFromCenter:F2}米");
                }
                
                if (firstImage.Enemies.Count > 5)
                {
                    Console.WriteLine($"\n... 还有 {firstImage.Enemies.Count - 5} 个敌人");
                }
                
                // ===== 示例：战术分析 =====
                Console.WriteLine("\n=== 战术分析 ===");
                var tacticGroups = battlefieldData.Images.GroupBy(img => img.TacticType);
                
                foreach (var tacticGroup in tacticGroups)
                {
                    var avgEnemies = tacticGroup.Average(img => img.EnemyCount);
                    var avgSpeed = tacticGroup.SelectMany(img => img.Enemies).Average(e => e.Speed);
                    
                    Console.WriteLine($"{tacticGroup.First().TacticNameCN}:");
                    Console.WriteLine($"  图片数量: {tacticGroup.Count()}");
                    Console.WriteLine($"  平均敌人数: {avgEnemies:F1}");
                    Console.WriteLine($"  平均速度: {avgSpeed:F2}米/秒");
                }
                
                // ===== 示例：地形查询 =====
                Console.WriteLine("\n=== 地形查询示例 ===");
                
                // 查找最大的建筑物
                var largestBuilding = battlefieldData.Terrain.Buildings
                    .OrderByDescending(b => b.Width * b.Depth)
                    .First();
                Console.WriteLine($"最大建筑物: ID {largestBuilding.Id}");
                Console.WriteLine($"  位置: ({largestBuilding.X:F2}, {largestBuilding.Z:F2})");
                Console.WriteLine($"  尺寸: {largestBuilding.Width:F2}m x {largestBuilding.Depth:F2}m");
                Console.WriteLine($"  高度: {largestBuilding.Height:F2}m");
                
                // 查找最长的巷道
                var longestAlley = battlefieldData.Terrain.Alleys
                    .OrderByDescending(a => a.Length)
                    .First();
                Console.WriteLine($"\n最长巷道: ID {longestAlley.Id}");
                Console.WriteLine($"  起点: ({longestAlley.StartX:F2}, {longestAlley.StartZ:F2})");
                Console.WriteLine($"  终点: ({longestAlley.EndX:F2}, {longestAlley.EndZ:F2})");
                Console.WriteLine($"  长度: {longestAlley.Length:F2}m");
                Console.WriteLine($"  宽度: {longestAlley.Width:F2}m");
                
                // ===== 示例：高级查询 =====
                Console.WriteLine("\n=== 高级查询示例 ===");
                
                // 找出所有包围战术的图片
                var encirclementImages = battlefieldData.Images
                    .Where(img => img.TacticType == "encirclement")
                    .ToList();
                Console.WriteLine($"包围战术图片: {encirclementImages.Count}张");
                
                // 找出所有距离用户超过20米的敌人
                var distantEnemies = battlefieldData.Images
                    .SelectMany(img => img.Enemies.Select(e => new { Image = img, Enemy = e }))
                    .Where(x => x.Enemy.DistanceFromCenter > 20)
                    .ToList();
                Console.WriteLine($"距离超过20米的敌人: {distantEnemies.Count}个");
                
                // 统计所有图片中的无人机总数
                int totalIFVs = battlefieldData.Images
                    .SelectMany(img => img.Enemies)
                    .Count(e => e.IsDrone);
                Console.WriteLine($"所有图片中共有无人机: {totalIFVs}个");
                
                // 找出移动最快的敌人
                var fastestEnemy = battlefieldData.Images
                    .SelectMany(img => img.Enemies.Select(e => new { Image = img, Enemy = e }))
                    .OrderByDescending(x => x.Enemy.Speed)
                    .First();
                Console.WriteLine($"\n移动最快的敌人:");
                Console.WriteLine($"  图片: {fastestEnemy.Image.Filename}");
                Console.WriteLine($"  类型: {(fastestEnemy.Enemy.IsDrone ? "无人机" : "士兵")}");
                Console.WriteLine($"  速度: {fastestEnemy.Enemy.Speed:F2}米/秒");
                
                Console.WriteLine("\n=== 数据读取完成 ===");
                
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
                Console.WriteLine($"堆栈跟踪: {ex.StackTrace}");
            }
        }
    }
}

