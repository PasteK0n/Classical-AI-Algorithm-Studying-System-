"""
data_exporter.py - 从 SQLite 对话/审查历史中提取高质量交互数据
支持单轮 Alpaca 格式、多轮 ShareGPT 格式、Dolly 企业级命令格式、COIG 中文安全数据格式导出以及格式转换工具
"""

import json
import sqlite3
import os
from typing import List, Dict, Any

# 1. 数据库转 Alpaca 格式 (instruction, input, output)
def export_db_to_alpaca(db_path: str, output_path: str):
    # 判断数据库是否存在
    if not os.path.exists(db_path):
        print(f'错误：找不到数据库文件 {db_path}')
        return
    
    # 数据库连接与游标建立
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # alpaca 数据存储
    alpaca_dataset = []

    try:
        # 查询并筛选高质量对话数据
        cursor.execute("SELECT question, answer FROM chat_history WHERE rating >= 4")
        rows = cursor.fetchall()

        # 存储为 alpaca 数据格式
        for q, a in rows:
            alpaca_dataset.append({
                "instruction": q,
                "input": "",
                "output": a
            })
    except Exception as e:
        print(f'Alpaca 数据库查询或处理过程中发生错误：{e}')
    finally:
        conn.close()

    # 将 alpaca_dataset 写入 output 文件
    if alpaca_dataset:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(alpaca_dataset, f, ensure_ascii=False, indent=2)
        print(f"成功导出 {len(alpaca_dataset)} 条 Alpaca 对话到 {output_path}")


# 2. 数据库转 ShareGPT 多轮对话格式 (conversations: human / gpt)
def export_db_to_sharegpt(db_path: str, output_path: str):
    # 判断数据库是否存在
    if not os.path.exists(db_path):
        print(f'错误：找不到数据库文件 {db_path}')
        return
    
    # 数据库连接与游标建立
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # shareGPT 数据存储
    sharegpt_dataset = []
    
    try:
        # 根据 session_id 对对话进行分组，升序排序
        cursor.execute("SELECT session_id, role, content FROM chat_messages ORDER BY session_id, created_at ASC")
        rows = cursor.fetchall()

        sessions = {}
        for session_id, role, content in rows:
            if session_id not in sessions:
                sessions[session_id] = []
            
            # 判断对话角色并映射
            role_tag = "human" if role in ["user", "human"] else "gpt"
            sessions[session_id].append({"from": role_tag, "value": content})
        
        # 筛选多轮对话 (>=2条消息) 并转换为 shareGPT 格式
        for session_id, conv in sessions.items():
            if len(conv) >= 2:
                sharegpt_dataset.append({
                    "conversations": conv
                })
    except Exception as e:
        print(f'ShareGPT 数据库查询或处理过程中发生错误：{e}')
    finally:
        conn.close()
    
    # 将 sharegpt_dataset 写入 output 文件
    if sharegpt_dataset:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(sharegpt_dataset, f, ensure_ascii=False, indent=2)
        print(f"成功导出 {len(sharegpt_dataset)} 条 ShareGPT 多轮对话到 {output_path}")


# 3. 数据库转 Dolly 企业级命令格式 (instruction, context, response)
def export_db_to_dolly(db_path: str, output_path: str):
    if not os.path.exists(db_path):
        print(f'错误：找不到数据库文件 {db_path}')
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    dolly_dataset = []

    try:
        cursor.execute("SELECT question, answer FROM chat_history WHERE rating >= 4")
        rows = cursor.fetchall()
        for q, a in rows:
            dolly_dataset.append({
                "instruction": q,
                "context": "",
                "response": a
            })
    except Exception as e:
        print(f'Dolly 数据库查询或处理过程中发生错误：{e}')
    finally:
        conn.close()

    if dolly_dataset:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dolly_dataset, f, ensure_ascii=False, indent=2)
        print(f"成功导出 {len(dolly_dataset)} 条 Dolly 格式数据到 {output_path}")


# 4. 数据库转 COIG 中文安全开放指令格式 (instruction, input, output, task_type)
def export_db_to_coig(db_path: str, output_path: str):
    if not os.path.exists(db_path):
        print(f'错误：找不到数据库文件 {db_path}')
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    coig_dataset = []

    try:
        cursor.execute("SELECT question, answer FROM chat_history WHERE rating >= 4")
        rows = cursor.fetchall()
        for q, a in rows:
            coig_dataset.append({
                "instruction": q,
                "input": "",
                "output": a,
                "task_type": "AI算法辅导"
            })
    except Exception as e:
        print(f'COIG 数据库查询或处理过程中发生错误：{e}')
    finally:
        conn.close()

    if coig_dataset:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(coig_dataset, f, ensure_ascii=False, indent=2)
        print(f"成功导出 {len(coig_dataset)} 条 COIG 格式数据到 {output_path}")


if __name__ == "__main__":
    dir_path = os.path.dirname(__file__)

    # 拼装数据库与目标 json 路径
    db_file = os.path.join(dir_path, "../../data/history.db")
    alpaca_out = os.path.join(dir_path, "../data/train_data.json")
    sharegpt_out = os.path.join(dir_path, "../data/train_data_sharegpt.json")
    dolly_out = os.path.join(dir_path, "../data/train_data_dolly.json")
    coig_out = os.path.join(dir_path, "../data/train_data_coig.json")

    # 执行 4 种主流格式一键导出
    print("=== 开始导出多格式 SFT 训练数据 ===")
    export_db_to_alpaca(db_file, alpaca_out)
    export_db_to_sharegpt(db_file, sharegpt_out)
    export_db_to_dolly(db_file, dolly_out)
    export_db_to_coig(db_file, coig_out)
    print("=== 数据导出完成 ===")
