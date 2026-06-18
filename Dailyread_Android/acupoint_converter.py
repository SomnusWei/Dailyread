#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
穴位数据导入工具 - Excel转JSON
用于为DailyRead Android应用生成穴位数据JSON文件
"""

import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import os
import sys

try:
    import pandas as pd
except ImportError:
    print("正在安装pandas...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
    import pandas as pd

try:
    import openpyxl
except ImportError:
    print("正在安装openpyxl...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
    import openpyxl


class AcupointConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("穴位数据导入工具")
        self.root.geometry("700x500")
        
        # Excel模板列名（与Excel保持一致）
        self.excel_columns = [
            "穴位",
            "经络",
            "穴性",
            "定位",
            "功效",
            "主治",
            "解剖",
            "操作",
            "禁忌",
            "穴位定位图路径",
            "备注"
        ]
        
        # JSON字段名
        self.json_fields = [
            "acupoint",
            "meridian",
            "acupointProperty",
            "location",
            "function",
            "indications",
            "anatomy",
            "operation",
            "contraindications",
            "locationImagePath",
            "note"
        ]
        
        self.create_widgets()
    
    def get_safe_value(self, row, column_name):
        """安全获取单元格值，避免NaN"""
        value = row.get(column_name, "")
        if pd.isna(value) or value is None or str(value).strip().lower() in ['nan', 'none', '']:
            return ""
        return str(value)
    
    def create_widgets(self):
        # 标题
        title_frame = ttk.Frame(self.root, padding="20")
        title_frame.pack(fill=tk.X)
        
        ttk.Label(
            title_frame,
            text="穴位数据导入工具",
            font=("Microsoft YaHei", 16, "bold")
        ).pack()
        
        ttk.Label(
            title_frame,
            text="将Excel文件转换为DailyRead可导入的JSON格式",
            font=("Microsoft YaHei", 10),
            foreground="#666666"
        ).pack(pady=(5, 0))
        
        # 主内容区
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 1. 导出模板区域
        template_frame = ttk.LabelFrame(main_frame, text="步骤1: 导出Excel模板", padding="15")
        template_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(
            template_frame,
            text="点击下方按钮导出Excel模板，填写数据后再进行转换",
            font=("Microsoft YaHei", 9)
        ).pack(anchor=tk.W)
        
        ttk.Button(
            template_frame,
            text="导出Excel模板",
            command=self.export_template,
            width=20
        ).pack(pady=(10, 0))
        
        # 2. 转换区域
        convert_frame = ttk.LabelFrame(main_frame, text="步骤2: Excel转JSON", padding="15")
        convert_frame.pack(fill=tk.BOTH, expand=True)
        
        # 文件选择
        file_frame = ttk.Frame(convert_frame)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(file_frame, text="选择Excel文件:").pack(anchor=tk.W)
        
        self.excel_path = tk.StringVar()
        path_entry = ttk.Entry(file_frame, textvariable=self.excel_path, state="readonly")
        path_entry.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(
            file_frame,
            text="浏览...",
            command=self.browse_excel
        ).pack(anchor=tk.W, pady=(5, 0))
        
        # ID设置
        id_frame = ttk.Frame(convert_frame)
        id_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(id_frame, text="起始ID:").pack(anchor=tk.W)
        
        self.start_id = tk.IntVar(value=1)
        id_spinbox = ttk.Spinbox(
            id_frame,
            from_=1,
            to=999999,
            textvariable=self.start_id,
            width=20
        )
        id_spinbox.pack(anchor=tk.W, pady=(5, 0))
        
        ttk.Label(
            id_frame,
            text="建议: 如果已有数据，请选择大于现有最大ID的数值",
            font=("Microsoft YaHei", 8),
            foreground="#666666"
        ).pack(anchor=tk.W, pady=(3, 0))
        
        # 转换按钮
        button_frame = ttk.Frame(convert_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="转换为JSON",
            command=self.convert_to_json,
            width=20
        ).pack(anchor=tk.W)
        
        # 提示信息
        info_frame = ttk.LabelFrame(main_frame, text="使用说明", padding="15")
        info_frame.pack(fill=tk.X, pady=(15, 0))
        
        info_text = (
            "1. 点击'导出Excel模板'获取标准模板\n"
            "2. 在Excel中填写穴位信息（穴位和经络为必填项）\n"
            "3. 选择填写好的Excel文件\n"
            "4. 设置起始ID（首次使用可保持1）\n"
            "5. 点击'转换为JSON'生成可导入文件\n"
            "6. 在APP中使用导入功能导入生成的JSON文件"
        )
        ttk.Label(
            info_frame,
            text=info_text,
            font=("Microsoft YaHei", 9),
            justify=tk.LEFT
        ).pack(anchor=tk.W)
    
    def export_template(self):
        """导出Excel模板"""
        file_path = filedialog.asksaveasfilename(
            title="保存Excel模板",
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
            initialfile="穴位数据模板.xlsx"
        )
        
        if not file_path:
            return
        
        try:
            # 创建示例数据
            sample_data = [
                {
                    "穴位": "合谷",
                    "经络": "手阳明大肠经",
                    "穴性": "原穴",
                    "定位": "在手背，第1、2掌骨间，当第2掌骨桡侧的中点处",
                    "功效": "疏风解表，通络镇痛，调理肠胃",
                    "主治": "头痛、目赤肿痛、齿痛、咽喉肿痛、口眼歪斜、热病无汗、多汗、腹痛、便秘、经闭、滞产",
                    "解剖": "在第1、2掌骨之间，第1骨间背侧肌中，深层有拇收肌横头；有手背静脉网，为头静脉的起部，腧穴近侧正当桡动脉从手背穿向手掌之处；布有桡神经浅支的掌背侧神经，深部有正中神经的指掌侧固有神经。",
                    "操作": "直刺0.5～1寸。孕妇禁针。",
                    "禁忌": "孕妇禁针",
                    "穴位定位图路径": "",
                    "备注": "常用穴位，为四总穴之一"
                },
                {
                    "穴位": "足三里",
                    "经络": "足阳明胃经",
                    "穴性": "合穴；胃下合穴",
                    "定位": "在小腿外侧，犊鼻下3寸，犊鼻与解溪连线上",
                    "功效": "健脾和胃，扶正培元，通经活络，升降气机",
                    "主治": "胃痛、呕吐、噎膈、腹胀、腹泻、痢疾、便秘、乳痈、肠痈、下肢痿痹、癫狂、虚劳诸证",
                    "解剖": "在胫骨前肌与趾长伸肌之间；有胫前动、静脉；为腓肠外侧皮神经及隐神经的皮支分布处，深层当腓深神经。",
                    "操作": "直刺1～2寸。",
                    "禁忌": "",
                    "穴位定位图路径": "",
                    "备注": "保健要穴，为四总穴之一"
                }
            ]
            
            # 创建DataFrame
            df = pd.DataFrame(sample_data, columns=self.excel_columns)
            
            # 确保没有NaN值
            df = df.fillna('')
            
            # 保存Excel
            df.to_excel(file_path, index=False, engine='openpyxl')
            
            messagebox.showinfo(
                "成功",
                f"Excel模板已成功导出！\n\n文件路径: {file_path}\n\n请在Excel中填写穴位信息后再进行转换。"
            )
            
        except Exception as e:
            messagebox.showerror("错误", f"导出Excel模板失败：\n{str(e)}")
    
    def browse_excel(self):
        """浏览选择Excel文件"""
        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )
        
        if file_path:
            self.excel_path.set(file_path)
    
    def convert_to_json(self):
        """转换Excel为JSON"""
        excel_file = self.excel_path.get()
        
        if not excel_file:
            messagebox.showwarning("警告", "请先选择Excel文件！")
            return
        
        if not os.path.exists(excel_file):
            messagebox.showerror("错误", "所选文件不存在！")
            return
        
        try:
            # 读取Excel
            df = pd.read_excel(excel_file, engine='openpyxl')
            
            # 将所有NaN替换为空字符串
            df = df.fillna('')
            
            # 检查列是否完整
            missing_columns = [col for col in self.excel_columns if col not in df.columns]
            if missing_columns:
                messagebox.showerror(
                    "错误",
                    f"Excel文件缺少必要的列：\n{', '.join(missing_columns)}\n\n请使用导出的模板。"
                )
                return
            
            # 构建JSON数据
            acupoints = []
            current_id = self.start_id.get()
            create_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            
            for idx, row in df.iterrows():
                # 获取穴位和经络（必填）
                acupoint = self.get_safe_value(row, "穴位").strip()
                meridian = self.get_safe_value(row, "经络").strip()
                
                if not acupoint or not meridian:
                    messagebox.showwarning(
                        "警告",
                        f"第 {idx + 2} 行：穴位和经络为必填项，已跳过该行！"
                    )
                    continue
                
                # 构建穴位数据
                acupoint_data = {
                    "id": current_id,
                    "acupoint": acupoint,
                    "meridian": meridian,
                    "acupointProperty": self.get_safe_value(row, "穴性").strip(),
                    "location": self.get_safe_value(row, "定位").strip(),
                    "function": self.get_safe_value(row, "功效").strip(),
                    "indications": self.get_safe_value(row, "主治").strip(),
                    "anatomy": self.get_safe_value(row, "解剖").strip(),
                    "operation": self.get_safe_value(row, "操作").strip(),
                    "contraindications": self.get_safe_value(row, "禁忌").strip(),
                    "locationImagePath": self.get_safe_value(row, "穴位定位图路径").strip() or None,
                    "note": self.get_safe_value(row, "备注").strip(),
                    "createTime": create_time
                }
                
                acupoints.append(acupoint_data)
                current_id += 1
            
            if not acupoints:
                messagebox.showwarning("警告", "没有有效的穴位数据！")
                return
            
            # 构建完整的JSON结构
            export_data = {
                "version": 2,
                "exportTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "dataType": "acupoints",
                "config": None,
                "contents": [],
                "checkIns": [],
                "acupoints": acupoints
            }
            
            # 保存JSON
            save_path = filedialog.asksaveasfilename(
                title="保存JSON文件",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
                initialfile=f"daily_read_acupoints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            if not save_path:
                return
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo(
                "成功",
                f"JSON文件已成功生成！\n\n"
                f"文件路径: {save_path}\n"
                f"成功转换: {len(acupoints)} 个穴位\n"
                f"ID范围: {self.start_id.get()} - {current_id - 1}\n\n"
                f"请在APP中使用导入功能导入此文件。"
            )
            
        except Exception as e:
            messagebox.showerror("错误", f"转换失败：\n{str(e)}")


def main():
    root = tk.Tk()
    
    # 设置应用图标（如果有的话）
    try:
        # 可以添加图标
        pass
    except:
        pass
    
    app = AcupointConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
