
import os
import json
import datetime
from typing import List, Optional, Dict, Any
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Relay-MCP")

# Constants for file names
FEATURE_LIST_FILE = "feature_list.json"
PROGRESS_FILE = "progress.txt"
INIT_SCRIPT_FILE = "init.sh" # or init.bat depending on OS, but spec says init.sh

def _get_feature_list_path() -> str:
    return os.path.join(os.getcwd(), FEATURE_LIST_FILE)

def _get_progress_path() -> str:
    return os.path.join(os.getcwd(), PROGRESS_FILE)

def _load_feature_list() -> Dict[str, Any]:
    path = _get_feature_list_path()
    if not os.path.exists(path):
        return {"project_status": "not_started", "tasks": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
         return {"project_status": "error", "tasks": [], "error": "Invalid JSON"}

def _save_feature_list(data: Dict[str, Any]):
    path = _get_feature_list_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def _append_progress(content: str):
    path = _get_progress_path()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n[{timestamp}] {content}\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(entry)

@mcp.tool()
def init_project(goal: str, initial_tasks: List[Dict[str, Any]]) -> str:
    """
    Initialize the Relay project with a goal and initial tasks.
    Creates feature_list.json and progress.txt.
    
    Args:
        goal: The main goal of the project.
        initial_tasks: A list of task dictionaries. Each task should have:
                       id, name, description, priority, status (pending), dependencies (list of ids).
    """
    # 1. Create feature_list.json
    feature_data = {
        "project_status": "in_progress",
        "goal": goal,
        "tasks": initial_tasks
    }
    _save_feature_list(feature_data)
    
    # 2. Create progress.txt
    with open(_get_progress_path(), "w", encoding="utf-8") as f:
        f.write(f"Project Started: {goal}\n")
        f.write("=" * 50 + "\n")
    
    _append_progress("Project initialized. Artifacts created.")
    
    # 3. Create init.sh (placeholder as per spec)
    with open(os.path.join(os.getcwd(), INIT_SCRIPT_FILE), "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n# Environment initialization script\necho 'Initializing environment...'\n")
        
    return "Project initialized successfully with feature_list.json and progress.txt."

@mcp.tool()
def read_state() -> str:
    """
    Reads the current state of the project.
    Returns a summary of feature_list.json and the last few lines of progress.txt.
    Use this to orient yourself (Load & Sync).
    """
    feature_list = _load_feature_list()
    
    # Read progress.txt (last 20 lines)
    progress_content = ""
    if os.path.exists(_get_progress_path()):
        with open(_get_progress_path(), "r", encoding="utf-8") as f:
            lines = f.readlines()
            progress_content = "".join(lines[-20:])
    else:
        progress_content = "No progress log found."

    return f"""
=== FEATURE LIST STATUS ===
Project Status: {feature_list.get('project_status', 'unknown')}
Total Tasks: {len(feature_list.get('tasks', []))}
Pending Tasks: {len([t for t in feature_list.get('tasks', []) if t.get('status') == 'pending'])}
Completed Tasks: {len([t for t in feature_list.get('tasks', []) if t.get('status') == 'completed'])}

=== RECENT PROGRESS LOG ===
{progress_content}
    """

@mcp.tool()
def get_feature_list() -> Dict[str, Any]:
    """Returns the full feature_list.json content."""
    return _load_feature_list()

@mcp.tool()
def get_next_task() -> str:
    """
    Finds the highest priority pending task whose dependencies are met.
    Returns the task details as a JSON string or a message if no task is available.
    """
    data = _load_feature_list()
    tasks = data.get("tasks", [])
    
    # Filter pending tasks
    pending_tasks = [t for t in tasks if t.get("status") == "pending"]
    if not pending_tasks:
        return "No pending tasks available."
    
    # Sort by priority (ascending, 1 is highest)
    pending_tasks.sort(key=lambda x: x.get("priority", 999))
    
    # Check dependencies
    completed_ids = {t["id"] for t in tasks if t.get("status") == "completed"}
    
    for task in pending_tasks:
        deps = task.get("dependencies", [])
        if all(d in completed_ids for d in deps):
            return json.dumps(task, indent=2, ensure_ascii=False)
            
    return "No pending tasks with satisfied dependencies found."

@mcp.tool()
def add_task(id: str, name: str, description: str, priority: int, dependencies: List[str] = []) -> str:
    """
    Adds a new task to the feature list.
    """
    data = _load_feature_list()
    # Check if ID exists
    if any(t["id"] == id for t in data.get("tasks", [])):
        return f"Error: Task ID {id} already exists."
    
    new_task = {
        "id": id,
        "name": name,
        "description": description,
        "priority": priority,
        "status": "pending",
        "dependencies": dependencies
    }
    
    data.setdefault("tasks", []).append(new_task)
    _save_feature_list(data)
    _append_progress(f"Added task: {id} - {name}")
    return f"Task {id} added successfully."

@mcp.tool()
def complete_task(task_id: str, summary: str, next_step_hint: str = "") -> str:
    """
    Marks a task as completed and updates the progress log.
    
    Args:
        task_id: The ID of the task to complete.
        summary: A description of what was done (Context).
        next_step_hint: Advice or warnings for the next worker (Hint).
    """
    data = _load_feature_list()
    tasks = data.get("tasks", [])
    
    task_found = False
    for task in tasks:
        if task["id"] == task_id:
            if task["status"] == "completed":
                return f"Task {task_id} is already completed."
            task["status"] = "completed"
            task_found = True
            break
    
    if not task_found:
        return f"Error: Task {task_id} not found."
        
    _save_feature_list(data)
    
    log_entry = f"COMPLETED {task_id}: {summary}"
    if next_step_hint:
        log_entry += f"\n   HINT: {next_step_hint}"
        
    _append_progress(log_entry)
    
    return f"Task {task_id} marked as completed."

@mcp.tool()
def update_task_status(task_id: str, status: str) -> str:
    """
    Manually updates a task's status (e.g., to 'executing' or 'blocked').
    """
    data = _load_feature_list()
    tasks = data.get("tasks", [])
    
    for task in tasks:
        if task["id"] == task_id:
            old_status = task.get("status")
            task["status"] = status
            _save_feature_list(data)
            _append_progress(f"Task {task_id} status changed: {old_status} -> {status}")
            return f"Task {task_id} status updated to {status}."
            
    return f"Error: Task {task_id} not found."

if __name__ == "__main__":
    mcp.run(transport='stdio')
