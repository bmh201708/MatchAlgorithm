# 威胁匹配触觉反馈系统

## 项目简介

这是一个Python项目，通过UDP服务器接收游戏数据，使用威胁评估算法选择最有威胁的敌人，并通过串口发送触觉震动信号给用户。

## 功能特性

- UDP服务器监听5005端口接收游戏数据
- **🤖 AI智能威胁评估**：使用GPT-4o分析战场情况，智能判断最危险的敌人
- **🧭 方向感知震动**：根据敌人方向自动选择对应的震动马达（0-7号，8个方向）
- 备用算法：当API不可用时自动切换到传统算法
- 硬件测试：启动时可选择测试所有振动器（0-7号）
- 通过COM7串口发送触觉震动信号
- 完整的错误处理和日志记录

## 项目结构

```
MatchAlgorithm/
├── main.py              # 主程序入口
├── threat_analyzer.py   # 威胁评估算法模块
├── direction_mapper.py  # 方向计算和马达映射模块
├── serial_handler.py    # 串口通信模块
├── udp_server.py        # UDP服务器模块
├── models.py            # 数据模型定义
├── requirements.txt     # 依赖包列表
└── README.md           # 项目说明文档
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置OpenAI API Key（可选）

为了使用GPT-4o智能威胁评估功能，需要配置OpenAI API Key：

### Windows:
```bash
set OPENAI_API_KEY=your-api-key-here
set OPENAI_BASE_URL=https://api.chatanywhere.tech/v1/
```

### Linux/Mac:
```bash
export OPENAI_API_KEY=your-api-key-here
export OPENAI_BASE_URL=https://api.chatanywhere.tech/v1/
```

### 永久配置（推荐）:
在系统环境变量中添加：
- `OPENAI_API_KEY`: 你的API密钥
- `OPENAI_BASE_URL`: API基础URL（默认: `https://api.chatanywhere.tech/v1/`）

**注意**: 
- 如果未配置API Key，系统会自动使用传统算法作为备用方案
- Base URL默认使用 `https://api.chatanywhere.tech/v1/`，也可以使用官方API `https://api.openai.com/v1`

## 使用方法

1. 确保COM7串口设备已连接
2. （可选）配置OpenAI API Key以启用AI威胁评估
3. 运行主程序：
   ```bash
   python main.py
   ```
4. 选择是否进行硬件测试（Y/N）
5. 程序将在5005端口监听UDP数据
6. 接收到数据后，会自动分析威胁并发送震动信号

## 数据格式

接收的JSON数据格式：

```json
{
  "round": 1,
  "playerPosition": {
    "x": 0.0,
    "y": 0.0,
    "z": 0.0
  },
  "targets": [
    {
      "id": 1,
      "angle": 45.23,
      "distance": 12.50,
      "type": "Tank",
      "position": {"x": 10.5, "y": 0.0, "z": 8.3}
    }
  ]
}
```

## 威胁评估算法

### 🤖 AI模式（GPT-4o）

当配置了OpenAI API Key时，系统会使用GPT-4o进行智能威胁评估：
- 综合分析敌人的位置、距离、角度、类型
- 考虑战术因素，做出更智能的判断
- 响应时间：通常0.5-2秒

### 📊 传统算法模式（备用）

当API不可用时，使用传统威胁度计算公式：

```
威胁度 = (1 / (距离 + 1)) × (1 / (|角度| + 1)) × 类型因子
```

- 距离因子：距离越近威胁越大
- 角度因子：角度越小（正前方）威胁越大
- 类型因子：Tank = 2.0, Soldier = 1.0
- 响应时间：毫秒级

## 硬件测试

程序启动时会询问是否进行硬件测试：
- 输入 `Y`：依次测试0-7号振动器，每个震动1秒（高强度255）
- 输入 `N`：跳过测试，直接进入主循环
- 测试格式：`0 255\n` → `0 0\n` → `1 255\n` → `1 0\n` ... → `7 0\n`

## 震动信号格式

发送到串口的格式：`X Y\n`
- X: 振动器编号（0-7，**根据敌人方向自动选择**）
- Y: 震动强度（0/200/255）
  - 255: 高威胁
  - 200: 低威胁
  - 0: 停止震动
- 震动持续时间：0.5秒（自动发送停止信号）

### 🧭 马达方向布局（俯视图，顺时针）

```
        0° (Z+)
     7     0     1
      \    |    /
270° — 6   玩   2 — 90° (X+)
      /    家   \
     5     4     3
       180° (Z-)
```

**马达对应方向**：
- **0号**：正前方 (0°, Z轴正方向)
- **1号**：前右 (45°)
- **2号**：正右 (90°, X轴正方向)
- **3号**：后右 (135°)
- **4号**：正后 (180°, Z轴负方向)
- **5号**：后左 (225°)
- **6号**：正左 (270°, X轴负方向)
- **7号**：前左 (315°)

系统会自动计算最具威胁敌人的方向，选择最接近的马达进行震动。

## 配置说明

- **OpenAI API**: 通过环境变量 `OPENAI_API_KEY` 配置（可选）
- **UDP端口**: 5005（可在`udp_server.py`中修改）
- **串口**: COM7（可在`main.py`中修改）
- **波特率**: 9600（可在`main.py`中修改）
- **马达数量**: 8个，编号0-7，对应8个方向
- **震动持续时间**: 0.5秒（可在`serial_handler.py`中修改）

## 注意事项

- 确保COM7串口设备已正确连接
- 确保5005端口未被占用
- 如需使用AI威胁评估，需配置有效的OpenAI API Key
- OpenAI API调用会产生费用（GPT-4o约$0.0025-0.01/次）
- 程序运行时会持续监听，使用Ctrl+C退出

## 工作流程

```
启动程序
    ↓
连接UDP服务器(5005端口)
    ↓
连接串口(COM7)
    ↓
硬件测试(可选) → 测试0-7号振动器
    ↓
等待UDP数据
    ↓
接收游戏数据 → 玩家位置 + 敌人列表
    ↓
威胁分析 → [GPT-4o AI分析] 或 [传统算法]
    ↓
选出最危险敌人
    ↓
计算敌人方向 → 映射到0-7号马达
    ↓
计算震动强度 → 255(高威胁) 或 200(低威胁)
    ↓
发送串口信号 → 对应方向马达震动0.5秒后停止
    ↓
循环继续...
```

---

## 📊 巷道战场图片生成器

位于 `/Generate_Picture/` 文件夹，用于生成包含战术意图的巷道战场俯视图。

### 🚀 使用方法

```bash
cd Generate_Picture
python generate_urban_battlefield_images.py
```

### 📁 输出文件

- **30张PNG图片**：3种类型 × 10种战术
- **urban_battlefield_data.json**：完整的地形和敌人数据
- **CSharpUrbanExample.cs**：C#数据读取示例代码

### 🎯 图片类型

| 类型 | 敌人数量 | 速度范围 | 说明 |
|------|---------|---------|------|
| **Type1_Sparse** | 3 | 1-5 m/s | 稀疏场景，少量敌人 |
| **Type2_Dense** | 30 | 1-5 m/s | 密集场景，常规速度 |
| **Type3_Fast** | 30 | 5-20 m/s | 密集场景，高速运动 |

### ⚔️ 战术类型（10种）

1. **Encirclement (包围)** - 环形包围用户
2. **Pincer (钳形攻势)** - 两翼夹击
3. **Ambush (伏击)** - 隐蔽待机，突然袭击
4. **Retreat (撤退)** - 远离用户
5. **Frontal Assault (正面突击)** - 直接冲锋
6. **Flanking (侧翼包抄)** - 从侧面包抄
7. **Defensive (防御阵型)** - 防守态势
8. **Guerrilla (游击骚扰)** - 机动性强，速度偏慢
9. **Pursuit (追击)** - 紧跟用户
10. **Dispersed (分散机动)** - 分散分布

### 📋 JSON数据格式

#### 敌人数据结构

```json
{
  "id": 1,                    // 敌人编号（从1开始）
  "type": "soldier",          // 类型："soldier" 或 "ifv"
  "x": 12.5,                  // X坐标（米）
  "z": -8.3,                  // Z坐标（米）
  "speed": 5.2,               // 移动速度（米/秒）
  "direction": 135.0          // 移动方向（度，0-360）
}
```

#### C#读取示例

```csharp
// 读取JSON文件
var jsonContent = File.ReadAllText("urban_battlefield_data.json");
var battlefieldData = JsonConvert.DeserializeObject<UrbanBattlefieldData>(jsonContent);

// 遍历图片
foreach (var image in battlefieldData.Images)
{
    Console.WriteLine($"图片: {image.Filename}");
    Console.WriteLine($"战术: {image.TacticNameCN}");
    
    // 遍历敌人
    foreach (var enemy in image.Enemies)
    {
        Console.WriteLine($"敌人 #{enemy.Id}:");
        Console.WriteLine($"  类型: {(enemy.IsIFV ? "步兵战车" : "士兵")}");
        Console.WriteLine($"  位置: ({enemy.X:F2}, {enemy.Z:F2})");
        Console.WriteLine($"  速度: {enemy.Speed:F2} m/s");
        Console.WriteLine($"  方向: {enemy.Direction:F2}°");
    }
}
```

### 🎨 图片特征

#### 敌人标注
- **士兵**：橙红色圆圈 (🟠)，图标内显示编号
- **IFV（步兵战车）**：紫色方块 (🟣)，图标内显示编号
- **速度标注**：黄色文字，显示在移动箭头末端
- **方向箭头**：黄色箭头，指示移动方向

#### 地形元素
- **建筑物**：深灰色矩形，标注建筑编号（B1, B2...）
- **巷道**：浅灰色通道
- **障碍物**：
  - 掩体 (Cover)：棕色三角形
  - 路障 (Barrier)：黑色矩形
  - 车辆 (Vehicle)：深蓝色矩形

#### 其他元素
- **玩家位置**：红色五角星 (⭐)，位于地图中心 (0, 0)
- **同心圆**：蓝色虚线，半径10米和20米
- **图例**：右上角，显示所有元素类型

### 🔧 碰撞检测

系统自动避免敌人重叠：
- **士兵 ↔ 士兵**：最小间距 6.0米
- **士兵 ↔ IFV**：最小间距 8.5米
- **IFV ↔ IFV**：最小间距 11.0米
- **IFV ↔ 建筑物**：5米缓冲区
- **IFV ↔ 障碍物**：不允许重叠

### 📐 坐标系统

- **平面**：xOz（俯视图）
- **原点**：玩家位置 (0, 0)
- **范围**：±50米
- **X轴**：东西方向（正方向为东）
- **Z轴**：南北方向（正方向为北）

