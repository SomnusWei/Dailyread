#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DailyRead数据导入工具 - Excel转JSON
用于为DailyRead Android应用生成文章和穴位数据JSON文件
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


class DataConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DailyRead数据导入工具")
        self.root.geometry("800x600")
        
        # 当前选中的数据库类型
        self.current_db_type = tk.StringVar(value="articles")
        
        # ============ 文章数据库配置 ============
        self.article_excel_columns = [
            "标题",
            "内容",
            "内容HTML",
            "中文字数",
            "字体",
            "字号",
            "字体颜色",
            "加粗",
            "正在阅读",
            "必读",
            "必读日期",
            "使用独立完成率",
            "独立完成率"
        ]
        
        self.article_json_fields = [
            "title",
            "content",
            "contentHtml",
            "chineseChars",
            "fontFamily",
            "fontSize",
            "fontColor",
            "isBold",
            "isReading",
            "isRequired",
            "requiredDays",
            "useIndependentCheckRate",
            "independentCheckRate"
        ]
        
        # ============ 穴位数据库配置 ============
        self.acupoint_excel_columns = [
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
        
        self.acupoint_json_fields = [
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
    
    def get_bool_value(self, row, column_name):
        """获取布尔值"""
        value = self.get_safe_value(row, column_name)
        return value.lower() in ['true', '1', '是', 'yes', 'on']
    
    def get_int_value(self, row, column_name, default=0):
        """获取整数值"""
        value = self.get_safe_value(row, column_name)
        try:
            return int(value)
        except ValueError:
            return default
    
    def get_float_value(self, row, column_name, default=0.0):
        """获取浮点数值"""
        value = self.get_safe_value(row, column_name)
        try:
            return float(value)
        except ValueError:
            return default
    
    def create_widgets(self):
        # 标题
        title_frame = ttk.Frame(self.root, padding="20")
        title_frame.pack(fill=tk.X)
        
        ttk.Label(
            title_frame,
            text="DailyRead数据导入工具",
            font=("Microsoft YaHei", 16, "bold")
        ).pack()
        
        ttk.Label(
            title_frame,
            text="将Excel文件转换为DailyRead可导入的JSON格式",
            font=("Microsoft YaHei", 10),
            foreground="#666666"
        ).pack(pady=(5, 0))
        
        # 数据库选择标签页
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # 文章数据库标签页
        articles_frame = ttk.Frame(notebook, padding="10")
        notebook.add(articles_frame, text="文章数据库")
        self.create_db_tab(articles_frame, "articles")
        
        # 穴位数据库标签页
        acupoints_frame = ttk.Frame(notebook, padding="10")
        notebook.add(acupoints_frame, text="穴位数据库")
        self.create_db_tab(acupoints_frame, "acupoints")
    
    def create_db_tab(self, parent_frame, db_type):
        """创建数据库标签页内容"""
        # 1. 导出模板区域
        template_frame = ttk.LabelFrame(parent_frame, text="步骤1: 导出Excel模板", padding="15")
        template_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            template_frame,
            text=f"点击下方按钮导出{ '文章' if db_type == 'articles' else '穴位' }Excel模板，填写数据后再进行转换",
            font=("Microsoft YaHei", 9)
        ).pack(anchor=tk.W)
        
        ttk.Button(
            template_frame,
            text="导出Excel模板",
            command=lambda: self.export_template(db_type),
            width=20
        ).pack(pady=(10, 0))
        
        # 2. 读取JSON获取最后ID区域
        read_id_frame = ttk.LabelFrame(parent_frame, text="步骤2: 读取JSON获取最后ID", padding="15")
        read_id_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            read_id_frame,
            text=f"从现有JSON文件读取最后一个{ '文章' if db_type == 'articles' else '穴位' }的ID，用于确定新数据的起始ID",
            font=("Microsoft YaHei", 9)
        ).pack(anchor=tk.W)
        
        read_id_file_frame = ttk.Frame(read_id_frame)
        read_id_file_frame.pack(fill=tk.X, pady=(10, 0))
        
        json_path_var = tk.StringVar()
        json_path_entry = ttk.Entry(read_id_file_frame, textvariable=json_path_var, state="readonly")
        json_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            read_id_file_frame,
            text="浏览...",
            command=lambda: self.browse_json(db_type, json_path_var)
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        last_id_label_var = tk.StringVar(value="最后一个ID: -")
        ttk.Label(read_id_frame, textvariable=last_id_label_var, font=("Microsoft YaHei", 9)).pack(anchor=tk.W, pady=(5, 0))
        
        ttk.Button(
            read_id_frame,
            text="读取最后ID",
            command=lambda: self.read_last_id(db_type, json_path_var.get(), last_id_label_var),
            width=20
        ).pack(anchor=tk.W, pady=(5, 0))
        
        # 3. 转换区域
        convert_frame = ttk.LabelFrame(parent_frame, text="步骤3: Excel转JSON", padding="15")
        convert_frame.pack(fill=tk.BOTH, expand=True)
        
        # 文件选择
        file_frame = ttk.Frame(convert_frame)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(file_frame, text="选择Excel文件:").pack(anchor=tk.W)
        
        excel_path_var = tk.StringVar()
        path_entry = ttk.Entry(file_frame, textvariable=excel_path_var, state="readonly")
        path_entry.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(
            file_frame,
            text="浏览...",
            command=lambda: self.browse_excel(excel_path_var)
        ).pack(anchor=tk.W, pady=(5, 0))
        
        # ID设置
        id_frame = ttk.Frame(convert_frame)
        id_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(id_frame, text="起始ID:").pack(anchor=tk.W)
        
        start_id_var = tk.IntVar(value=1)
        id_spinbox = ttk.Spinbox(
            id_frame,
            from_=1,
            to=999999,
            textvariable=start_id_var,
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
            command=lambda: self.convert_to_json(db_type, excel_path_var.get(), start_id_var.get()),
            width=20
        ).pack(anchor=tk.W)
        
        # 提示信息
        info_frame = ttk.LabelFrame(parent_frame, text="使用说明", padding="15")
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        if db_type == "articles":
            info_text = (
                "1. 点击'导出Excel模板'获取文章标准模板\n"
                "2. 在Excel中填写文章信息（标题和内容为必填项）\n"
                "3. （可选）读取现有JSON获取最后一个ID，确定起始ID\n"
                "4. 选择填写好的Excel文件\n"
                "5. 设置起始ID（首次使用可保持1）\n"
                "6. 点击'转换为JSON'生成可导入文件\n"
                "7. 在APP中使用导入功能导入生成的JSON文件"
            )
        else:
            info_text = (
                "1. 点击'导出Excel模板'获取穴位标准模板\n"
                "2. 在Excel中填写穴位信息（穴位和经络为必填项）\n"
                "3. （可选）读取现有JSON获取最后一个ID，确定起始ID\n"
                "4. 选择填写好的Excel文件\n"
                "5. 设置起始ID（首次使用可保持1）\n"
                "6. 点击'转换为JSON'生成可导入文件\n"
                "7. 在APP中使用导入功能导入生成的JSON文件"
            )
        
        ttk.Label(
            info_frame,
            text=info_text,
            font=("Microsoft YaHei", 9),
            justify=tk.LEFT
        ).pack(anchor=tk.W)
    
    def export_template(self, db_type):
        """导出Excel模板"""
        if db_type == "articles":
            default_name = "文章数据模板.xlsx"
            sample_data = [
                {
                    "标题": "示例文章1",
                    "内容": "这是一篇示例文章的内容...\n可以换行。",
                    "内容HTML": "",
                    "中文字数": "100",
                    "字体": "default",
                    "字号": "16",
                    "字体颜色": "#000000",
                    "加粗": "false",
                    "正在阅读": "true",
                    "必读": "false",
                    "必读日期": "",
                    "使用独立完成率": "false",
                    "独立完成率": "30.0"
                },
                {
                    "标题": "示例文章2",
                    "内容": "另一篇示例文章的内容...",
                    "内容HTML": "",
                    "中文字数": "150",
                    "字体": "default",
                    "字号": "16",
                    "字体颜色": "#000000",
                    "加粗": "false",
                    "正在阅读": "true",
                    "必读": "true",
                    "必读日期": "1,3,5",
                    "使用独立完成率": "true",
                    "独立完成率": "50.0"
                }
            ]
            columns = self.article_excel_columns
        else:
            default_name = "穴位数据模板.xlsx"
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
            columns = self.acupoint_excel_columns
        
        file_path = filedialog.asksaveasfilename(
            title="保存Excel模板",
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
            initialfile=default_name
        )
        
        if not file_path:
            return
        
        try:
            # 创建DataFrame
            df = pd.DataFrame(sample_data, columns=columns)
            
            # 确保没有NaN值
            df = df.fillna('')
            
            # 保存Excel
            df.to_excel(file_path, index=False, engine='openpyxl')
            
            messagebox.showinfo(
                "成功",
                f"Excel模板已成功导出！\n\n文件路径: {file_path}\n\n请在Excel中填写{ '文章' if db_type == 'articles' else '穴位' }信息后再进行转换。"
            )
            
        except Exception as e:
            messagebox.showerror("错误", f"导出Excel模板失败：\n{str(e)}")
    
    def browse_excel(self, excel_path_var):
        """浏览选择Excel文件"""
        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )
        
        if file_path:
            excel_path_var.set(file_path)
    
    def browse_json(self, db_type, json_path_var):
        """浏览选择JSON文件"""
        file_path = filedialog.askopenfilename(
            title="选择JSON文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            json_path_var.set(file_path)
    
    def read_last_id(self, db_type, json_file, last_id_label_var):
        """读取JSON文件获取最后一个ID"""
        if not json_file:
            messagebox.showwarning("警告", "请先选择JSON文件！")
            return
        
        if not os.path.exists(json_file):
            messagebox.showerror("错误", "所选文件不存在！")
            return
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            data_list = data.get("contents" if db_type == "articles" else "acupoints", [])
            
            if not data_list:
                last_id_label_var.set("最后一个ID: 0 (无数据)")
                messagebox.showinfo("提示", "JSON文件中没有数据，最后一个ID为0")
                return
            
            last_id = max(item.get("id", 0) for item in data_list)
            last_id_label_var.set(f"最后一个ID: {last_id}")
            
            messagebox.showinfo(
                "成功",
                f"最后一个{ '文章' if db_type == 'articles' else '穴位' }的ID: {last_id}\n\n建议下一个数据起始ID设为 {last_id + 1}"
            )
            
        except Exception as e:
            messagebox.showerror("错误", f"读取JSON文件失败：\n{str(e)}")
    
    def convert_to_json(self, db_type, excel_file, start_id):
        """转换Excel为JSON"""
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
            expected_columns = self.article_excel_columns if db_type == "articles" else self.acupoint_excel_columns
            missing_columns = [col for col in expected_columns if col not in df.columns]
            if missing_columns:
                messagebox.showerror(
                    "错误",
                    f"Excel文件缺少必要的列：\n{', '.join(missing_columns)}\n\n请使用导出的模板。"
                )
                return
            
            # 构建JSON数据
            data_list = []
            current_id = start_id
            create_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            
            for idx, row in df.iterrows():
                if db_type == "articles":
                    # 获取文章标题和内容（必填）
                    title = self.get_safe_value(row, "标题").strip()
                    content = self.get_safe_value(row, "内容").strip()
                    
                    if not title or not content:
                        messagebox.showwarning(
                            "警告",
                            f"第 {idx + 2} 行：标题和内容为必填项，已跳过该行！"
                        )
                        continue
                    
                    # 构建文章数据
                    article_data = {
                        "id": current_id,
                        "title": title,
                        "content": content,
                        "contentHtml": self.get_safe_value(row, "内容HTML").strip() or None,
                        "chineseChars": self.get_int_value(row, "中文字数"),
                        "fontFamily": self.get_safe_value(row, "字体").strip() or "default",
                        "fontSize": self.get_int_value(row, "字号", 16),
                        "fontColor": self.get_safe_value(row, "字体颜色").strip() or "#000000",
                        "isBold": self.get_bool_value(row, "加粗"),
                        "isReading": self.get_bool_value(row, "正在阅读"),
                        "isRequired": self.get_bool_value(row, "必读"),
                        "requiredDays": self.get_safe_value(row, "必读日期").strip(),
                        "useIndependentCheckRate": self.get_bool_value(row, "使用独立完成率"),
                        "independentCheckRate": self.get_float_value(row, "独立完成率", 30.0),
                        "createTime": create_time
                    }
                    
                    data_list.append(article_data)
                else:
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
                    
                    data_list.append(acupoint_data)
                
                current_id += 1
            
            if not data_list:
                messagebox.showwarning("警告", "没有有效的数据！")
                return
            
            # 构建完整的JSON结构
            export_data = {
                "version": 3,
                "exportTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "dataType": "articles" if db_type == "articles" else "acupoints",
                "config": None,
                "contents": data_list if db_type == "articles" else [],
                "checkIns": [],
                "acupoints": data_list if db_type == "acupoints" else []
            }
            
            # 保存JSON
            default_name = f"daily_read_{ 'articles' if db_type == 'articles' else 'acupoints' }_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            save_path = filedialog.asksaveasfilename(
                title="保存JSON文件",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
                initialfile=default_name
            )
            
            if not save_path:
                return
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo(
                "成功",
                f"JSON文件已成功生成！\n\n"
                f"文件路径: {save_path}\n"
                f"成功转换: {len(data_list)} 个{ '文章' if db_type == 'articles' else '穴位' }\n"
                f"ID范围: {start_id} - {current_id - 1}\n\n"
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
    
    app = DataConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
