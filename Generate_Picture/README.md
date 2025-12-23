# 战场形态图生成器

## 功能说明

本目录包含两个战场图片生成器：
1. **基础战场生成器** (`generate_battlefield_images.py`)：生成简单战场环境
2. **巷道战场生成器** (`generate_urban_battlefield_images.py`)：基于 TerrainData 生成包含建筑、巷道、障碍物的复杂城市战场环境

---

# 一、基础战场生成器

这个Python脚本可以自动生成战场形态图，用于模拟简单的游戏战场环境。

## 生成内容

脚本会生成**30张PNG图片**，分为三种类型：

### 类型1：少量敌人（10张）
- 文件名：`type1_sparse_01.png` ~ `type1_sparse_10.png`
- 敌人数量：3个
- 移动速度：正常（1-5米/秒）
- 敌人类型：士兵/坦克随机

### 类型2：密集敌人（10张）
- 文件名：`type2_dense_01.png` ~ `type2_dense_10.png`
- 敌人数量：30个
- 移动速度：正常（1-5米/秒）
- 敌人类型：士兵/坦克随机

### 类型3：快速移动（10张）
- 文件名：`type3_fast_01.png` ~ `type3_fast_10.png`
- 敌人数量：30个
- 移动速度：快速（10-20米/秒）
- 敌人类型：士兵/坦克随机

## 图片特性

每张图片包含：

### 基础元素
- **用户位置**：蓝色五角星，位于图片中心（0, 0）
- **同心圆**：半径10米和20米的虚线圆圈
- **坐标网格**：-30米到+30米的坐标系统

### 敌人表示
- **士兵**：橙红色圆圈 🟠（orangered）
- **坦克**：紫色方块 🟣（purple）
- **移动方向**：箭头指示
- **引导线**：从敌人位置到标注框的连线，颜色与敌人类型匹配
- **信息标注**：
  - 类别（士兵/坦克）
  - 坐标位置（x, y）米
  - 移动速度（米/秒）
  - 移动方向（度数，0-360°）
  - 标注框边框颜色与敌人类型对应

### 统计信息
- 左上角显示：总敌人数、士兵数、坦克数、平均速度
- 右上角显示：图例说明

## 使用方法

### 运行脚本
```bash
cd Generate_Picture
python generate_battlefield_images.py
```

### 输出文件
运行后会生成：
- **30张PNG图片**：战场形态图
- **1个JSON数据文件**：`battlefield_data.json`，包含所有图片和敌人的详细数据

### 依赖库
- matplotlib>=3.5.0
- numpy>=1.21.0

### 安装依赖
```bash
pip install matplotlib numpy
```

## 配置参数

可以在脚本中修改以下参数：

```python
IMAGE_SIZE = 1200      # 图片尺寸（像素）
COORD_RANGE = 30       # 坐标范围（米）
CIRCLE_RADII = [10, 20]  # 同心圆半径（米）
SPEED_NORMAL = (1, 5)    # 正常速度范围
SPEED_FAST = (10, 20)    # 快速速度范围
```

## 输出示例

### 类型1 - 少量敌人
3个敌人，布局稀疏，便于观察单个敌人详细信息

### 类型2 - 密集敌人
30个敌人，模拟复杂战场环境，测试密集目标情况

### 类型3 - 快速移动
30个敌人高速移动，模拟高强度战斗场景

## JSON数据文件

### 文件结构
`battlefield_data.json` 包含完整的战场数据，方便程序读取和分析：

```json
{
  "metadata": {
    "version": "1.0",
    "imageSize": 1200,
    "coordinateRange": 30,
    "circleRadii": [10, 20],
    "speedRanges": {
      "normal": {"min": 1, "max": 5},
      "fast": {"min": 10, "max": 20}
    },
    "totalImages": 30
  },
  "images": [
    {
      "imageId": "type1_01",
      "filename": "type1_sparse_01.png",
      "type": "Type1_Sparse",
      "enemyCount": 3,
      "speedRange": {"min": 1, "max": 5},
      "enemies": [
        {
          "type": "soldier",
          "x": -21.76,
          "y": 0.89,
          "speed": 1.02,
          "direction": 233.61
        }
      ]
    }
  ]
}
```

### C#读取示例

项目包含完整的C#示例代码 `CSharpExample.cs`，展示如何读取JSON数据：

```csharp
// 读取JSON文件
string jsonContent = File.ReadAllText("battlefield_data.json");
BattlefieldData data = JsonConvert.DeserializeObject<BattlefieldData>(jsonContent);

// 访问数据
foreach (var image in data.Images)
{
    Console.WriteLine($"图片: {image.Filename}");
    foreach (var enemy in image.Enemies)
    {
        Console.WriteLine($"  {enemy.Type}: ({enemy.X}, {enemy.Y})");
    }
}
```

**依赖包**：需要安装 `Newtonsoft.Json` NuGet包
```bash
Install-Package Newtonsoft.Json
```

## 文件清单

生成的文件：
- ✅ 10张类型1图片（少量敌人）
- ✅ 10张类型2图片（密集敌人）
- ✅ 10张类型3图片（快速移动）
- ✅ 1个JSON数据文件（battlefield_data.json）
- ✅ 1个C#示例代码（CSharpExample.cs）

总计：**30张PNG图片** + **1个JSON数据文件** + **1个C#示例代码**

## 注意事项

1. 图片尺寸为1200x1200像素，PNG格式
2. 每次运行会覆盖已存在的同名文件
3. 敌人位置、类型、速度、方向均随机生成
4. 中文字体支持：脚本会自动尝试使用系统中文字体

## 技术细节

- 坐标系统：笛卡尔坐标系，用户在原点(0,0)
- 角度定义：0度为正东方向，逆时针旋转
- 最小安全距离：敌人不会生成在距离用户2米以内
- 边界限制：所有敌人都在±30米范围内

---

生成时间：约10-15秒
开发语言：Python 3.7+

---

# 二、巷道战场生成器（推荐）

## 功能说明

基于真实 TerrainData 地形数据生成包含建筑、巷道、障碍物的复杂城市战场环境，并展示10种不同的战术意图。

## 生成内容

脚本会生成**30张PNG图片** + **1个JSON数据文件**，分为三种类型：

### 类型1：少量敌人（10张）
- 文件名：`type1_tactic_TACTICNAME_01.png` ~ `type1_tactic_TACTICNAME_10.png`
- 敌人数量：3个
- 移动速度：正常（1-5米/秒）
- 敌人类型：士兵/坦克随机
- **10种战术**：每张图片展示不同的战术意图

### 类型2：密集敌人（10张）
- 文件名：`type2_tactic_TACTICNAME_01.png` ~ `type2_tactic_TACTICNAME_10.png`
- 敌人数量：30个
- 移动速度：正常（1-5米/秒）
- 敌人类型：士兵/坦克随机
- **10种战术**：每张图片展示不同的战术意图

### 类型3：快速移动（10张）
- 文件名：`type3_tactic_TACTICNAME_01.png` ~ `type3_tactic_TACTICNAME_10.png`
- 敌人数量：30个
- 移动速度：快速（10-20米/秒）
- 敌人类型：士兵/坦克随机
- **10种战术**：每张图片展示不同的战术意图

## 10种战术类型

每种类型的10张图片对应10种不同的战术意图：

| 编号 | 战术英文名 | 战术中文名 | 特征描述 |
|------|------------|------------|----------|
| 1 | Encirclement | 包围 | 敌人均匀分布在用户周围360度，形成包围圈 |
| 2 | Pincer | 钳形攻势 | 敌人分为左右两翼，从侧面包抄 |
| 3 | Ambush | 伏击 | 敌人隐藏在建筑和障碍物后，集中在某个方向 |
| 4 | Retreat | 撤退 | 敌人分散分布，移动方向背离用户 |
| 5 | Frontal Assault | 正面突击 | 敌人集中在前方，排成多个波次直冲用户 |
| 6 | Flanking | 侧翼包抄 | 敌人从左侧或右侧呈弧形包抄 |
| 7 | Defensive | 防御阵型 | 敌人依托建筑物和掩体，形成交叉火力网 |
| 8 | Guerrilla | 游击骚扰 | 敌人分散在各个角落，利用地形不规则分布 |
| 9 | Pursuit | 追击 | 敌人从后方追赶，呈扇形展开 |
| 10 | Dispersed | 分散机动 | 敌人均匀分散，移动方向呈辐射状 |

## 图片特性

每张图片包含完整的城市战场环境：

### 地形元素（基于TerrainData）
- **建筑物**（7栋）：深灰色矩形，标注编号（B1-B7）
  - 包含墙体、门、窗户等详细结构
  - 3-4层楼高，提供立体作战空间
- **巷道**（6条）：浅灰色带状区域
  - 主干道和支路交错
  - 宽度9-12米不等
- **障碍物**（22个）：
  - 掩体（Cover）：棕色三角形
  - 路障（Barrier）：黑色矩形
  - 车辆（Vehicle）：深蓝色矩形

### 战术元素
- **用户位置**：红色五角星，位于图片中心（0, 0）
- **同心圆**：半径10米和20米的蓝色虚线圆圈
- **坐标系统**：xOz平面，范围 [-50, 50] 米

### 敌人表示
- **士兵（Soldier）**：橙红色圆圈 🟠
- **无人机（Drone）**：紫色方块 🟣（不会出现在建筑物内部）
- **移动方向**：黄色箭头指示
- **引导线**：从敌人位置到标注框的黑色连线
- **信息标注**：
  - 类别（Soldier/Tank）
  - 坐标位置 (x, z) 米
  - 移动速度 m/s
  - 移动方向 度数

### 图例说明
右上角包含完整的图例，包括：
- Player（玩家）
- Soldier（士兵）
- Drone（无人机）
- Building（建筑）
- Alley（巷道）
- Cover（掩体）
- Barrier（路障）
- Vehicle（车辆）

### 标题信息
图片标题格式：`Type_Label - Tactic: TACTIC_NAME (中文名) - N Enemies`

例如：`Type1_Sparse - Tactic: ENCIRCLEMENT (包围) - 3 Enemies`

## 使用方法

### 运行脚本
```bash
cd Generate_Picture
python generate_urban_battlefield_images.py
```

### 输出文件
运行后会生成：
- **30张PNG图片**：巷道战场形态图（每张约150-250KB）
- **1个JSON数据文件**：`urban_battlefield_data.json`（约245KB）

### 依赖库
```bash
pip install matplotlib numpy
```

## 配置参数

可以在脚本中修改以下参数：

```python
IMAGE_SIZE = 1600          # 图片尺寸（像素）
COORD_RANGE = 50           # 坐标范围（米）
CIRCLE_RADII = [10, 20]    # 同心圆半径（米）
SPEED_NORMAL = (1, 5)      # 正常速度范围
SPEED_FAST = (10, 20)      # 快速速度范围
```

## JSON数据文件

### 文件结构
`urban_battlefield_data.json` 包含完整的地形和战场数据：

```json
{
  "metadata": {
    "version": "2.0",
    "terrainFile": "TerrainData_20251219_191755.json",
    "coordinateSystem": "xOz",
    "imageSize": 1600,
    "coordinateRange": 50,
    "tactics": ["encirclement", "pincer", ...],
    "totalImages": 30
  },
  "terrain": {
    "buildings": [
      {
        "id": 1,
        "x": -37.71,
        "z": -31.68,
        "width": 22.58,
        "depth": 34.64,
        "height": 14.0
      }
    ],
    "alleys": [...],
    "obstacles": [...]
  },
  "images": [
    {
      "imageId": "type1_encirclement_01",
      "filename": "type1_tactic_encirclement_01.png",
      "type": "Type1_Sparse",
      "tacticType": "encirclement",
      "tacticNameCN": "包围",
      "enemyCount": 3,
      "enemies": [...]
    }
  ]
}
```

### C#读取示例

项目包含专门的C#示例代码 `CSharpUrbanExample.cs`，展示如何读取巷道战场数据：

```csharp
// 读取JSON文件
string jsonContent = File.ReadAllText("urban_battlefield_data.json");
UrbanBattlefieldData data = JsonConvert.DeserializeObject<UrbanBattlefieldData>(jsonContent);

// 访问地形数据
Console.WriteLine($"建筑物: {data.Terrain.Buildings.Count}栋");
Console.WriteLine($"巷道: {data.Terrain.Alleys.Count}条");
Console.WriteLine($"障碍物: {data.Terrain.Obstacles.Count}个");

// 访问图片和战术数据
foreach (var image in data.Images)
{
    Console.WriteLine($"战术: {image.TacticNameCN} ({image.TacticType})");
    Console.WriteLine($"敌人: {image.EnemyCount}个");
    
    // 统计士兵和无人机
    int soldiers = image.Enemies.Count(e => e.IsSoldier);
    int ifvs = image.Enemies.Count(e => e.IsDrone);
    Console.WriteLine($"  士兵: {soldiers}, 无人机: {ifvs}");
}

// 战术分析
var tacticGroups = data.Images.GroupBy(img => img.TacticType);
foreach (var group in tacticGroups)
{
    var avgSpeed = group.SelectMany(img => img.Enemies).Average(e => e.Speed);
    Console.WriteLine($"{group.First().TacticNameCN}: 平均速度 {avgSpeed:F2}m/s");
}
```

**依赖包**：需要安装 `Newtonsoft.Json` NuGet包
```bash
Install-Package Newtonsoft.Json
```

## 文件清单

生成的文件：
- ✅ 10张类型1图片（3个敌人，10种战术）
- ✅ 10张类型2图片（30个敌人，10种战术）
- ✅ 10张类型3图片（30个敌人高速，10种战术）
- ✅ 1个JSON数据文件（urban_battlefield_data.json，含地形数据）
- ✅ 1个C#示例代码（CSharpUrbanExample.cs）

总计：**30张PNG图片** + **1个JSON数据文件** + **1个C#示例代码**

## 技术特点

### 地形解析
- 自动解析 TerrainData JSON 文件
- 提取建筑物、巷道、障碍物的精确位置和尺寸
- 支持3D坐标到2D俯视图的投影转换

### 战术算法
- 10种专业战术分布算法
- 基于三角函数计算敌人最优位置
- 考虑地形因素（避免生成在建筑物内部）
- 每种战术有独特的移动方向和阵型特征

### 碰撞检测
- 确保敌人不会生成在建筑物内部
- 无人机需要额外的安全缓冲区（2米），不会紧贴建筑物
- 多次尝试机制（最多20次）找到有效位置
- 保持战术意图的同时适应地形约束

### 可视化优化
- 完整的图例系统
- 战术名称双语显示（中英文）
- 清晰的标注和引导线
- 适当的颜色对比和透明度

## 注意事项

1. **字体显示**：使用英文标签确保跨平台兼容性
2. **坐标系统**：xOz平面（x水平，z垂直），范围 [-50, 50] 米
3. **地形文件**：需要 `TerrainData_20251219_191755.json` 在同目录
4. **生成时间**：约30-40秒（因为包含复杂地形渲染和碰撞检测）
5. **文件覆盖**：每次运行会覆盖已存在的同名文件
6. **敌人类型**：
   - **士兵**：可以在任何位置出现
   - **无人机（Drone）**：不会出现在建筑物内部或紧贴建筑物的位置

## 应用场景

- ✅ 城市巷战战术训练
- ✅ CQB（近距离战斗）模拟
- ✅ 多层建筑清剿演练
- ✅ 战术AI测试数据集
- ✅ 游戏关卡设计参考
- ✅ 军事战术教学素材

---

## 对比：基础 vs 巷道战场生成器

| 特性 | 基础生成器 | 巷道生成器 |
|------|------------|------------|
| 地形环境 | 空旷平面 | 城市巷道（建筑+巷道+障碍物） |
| 战术意图 | 随机分布 | 10种专业战术 |
| 地形数据 | 无 | 完整TerrainData |
| 敌人分布 | 完全随机 | 战术导向+地形避让 |
| 图例系统 | 简单 | 完整详细 |
| 应用场景 | 基础测试 | 专业战术训练 |
| 推荐度 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**建议使用巷道战场生成器获得更专业的战术训练数据。**

---

开发语言：Python 3.7+
生成时间：约30-40秒

