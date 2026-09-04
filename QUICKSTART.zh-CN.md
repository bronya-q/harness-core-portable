# 快速开始（中文）

## 你需要什么

- Python 3.11 或更高版本
- 不需要 Ollama 也能跑离线演示
- 不需要 API key
- 不需要真实用户数据

## 5 分钟体验

```bash
git clone https://github.com/bronya-q/harness-core-portable.git
cd harness-core-portable
python harness.py start
```

启动后会看到菜单，选 **1. 体验离线演示** 即可。

或者直接运行：

```bash
python harness.py demo --offline
```

演示内容：

1. Alice 记住“蓝色钥匙在旧港钟楼下”
2. Bob 读不到 Alice 的私人记忆（角色隔离）
3. Alice/Bob 都知道“旧港终年有雾”（共享世界设定）
4. 蓝色钥匙 → 银色钥匙（纠错）
5. v1 → v2 → restore 出 v3（版本恢复）
6. 一键清理临时数据

## 环境检查

```bash
python harness.py doctor
```

## 查看数据

```bash
python harness.py data status
python harness.py inspect --scope character:alice
```

## 清理

```bash
python harness.py demo --reset
```

## 没装模型怎么办

- 离线演示、Notebook、Story Core、角色隔离、纠错、恢复都**不依赖模型**。
- 只有“AI 对话生成”需要本地 Ollama。
