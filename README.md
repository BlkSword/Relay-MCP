# Relay-MCP

这是一个基于「文件为中心的无限接力架构」的 MCP 服务器实现。它通过 `feature_list.json` 和 `progress.txt` 管理项目状态，使 LLM Agents 以无状态、原子化的方式协作。

## 安装

- 确保已安装 Python 3.10+。
- 安装依赖：
  ```bash
  pip install -r requirements.txt
  ```

## 使用

### 运行服务器

你可以使用 MCP CLI 运行该服务器，或将其集成到你的 MCP 客户端配置中。

```bash
# 使用 stdio 传输运行（默认）
python relay_server.py
```

### 与 Claude Desktop 配合使用

在 Claude Desktop 的设置中添加 MCP 服务器配置即可使用本项目。

**本地 Python 方式：**

将以下片段加入到 Claude Desktop 的配置文件中（例如 `settings.json`）：

```json
{
  "mcpServers": {
    "relay-mcp": {
      "command": "python",
      "args": [
        "relay_server.py"
      ]
    }
  }
}
```

将上面的 JSON 片段合并到你现有的 Claude Desktop 配置中即可。

### 提供的工具

该服务器向 LLM 暴露以下工具（Tools）：

1. **`init_project(goal, initial_tasks)`**
   - 初始化项目工件（`feature_list.json`、`progress.txt`、`init.sh`）。
   - 供 **Starter Agent** 使用。

2. **`read_state()`**
   - 读取当前项目状态与最新日志。
   - 供 **Worker Agent** 在 **Load & Sync** 阶段使用。

3. **`get_next_task()`**
   - 获取优先级最高且依赖已满足的 `pending` 任务。
   - 供 **Worker Agent** 在 **Decide** 阶段使用。

4. **`complete_task(task_id, summary, next_step_hint)`**
   - 将任务标记为 `completed`，并在日志中追加对下一位 Worker 的提示。
   - 供 **Worker Agent** 在 **Commit** 阶段使用。

5. **`add_task(id, name, description, priority, dependencies)`**
   - 向任务队列新增任务。
   - 适用于动态规划与扩展。

6. **`update_task_status(task_id, status)`**
   - 手动更新任务状态（如 `executing`、`blocked`）。

## 工作流示例

1. **Starter Agent** 调用 `init_project("Build Web App", [...tasks...])`。
2. **Worker 1** 启动：
   - 调用 `read_state()` → 查看项目为新启动。
   - 调用 `get_next_task()` → 获得「任务 1」。
   - 编码实现（将代码写入磁盘）。
   - 调用 `complete_task("Task 1", "完成 X", "注意 Y")`。
3. **Worker 2** 启动：
   - 调用 `read_state()` → 看到「任务 1」已完成，日志提示「注意 Y」。
   - 调用 `get_next_task()` → 获得「任务 2」。
   - ...

## 工件（Artifacts）

- `feature_list.json`：结构化任务队列。
- `progress.txt`：语义日志 / 思维链历史。
- `init.sh`：环境初始化脚本。
