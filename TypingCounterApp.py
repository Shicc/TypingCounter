import tkinter as tk
from tkinter import ttk, messagebox
import keyboard
from pynput import mouse
import time
import json
from datetime import datetime


class TypingCounterApp:

    def __init__(self, root):
        self.root = root
        self.root.title("键盘打字统计器")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # 设置窗口图标（如果有的话）
        try:
            self.root.iconbitmap("typing_icon.ico")
        except:
            pass  # 如果没有图标文件则跳过

        # 初始化变量
        self.typing_count = 0  # 本次运行总打字数（持续累加，不归零）
        self.saved_session_count = 0  # 本次运行中已保存的数量（用于计算增量）
        self.key_count = {}  # 新增：记录每个按键的按下次数
        # 新增：鼠标按键计数
        self.mouse_count = {
            "left": 0,
            "right": 0,
            "forward": 0,  # 前进（通常是侧键 XButton1）
            "back": 0,  # 后退（通常是侧键 XButton2）
            "scroll_up": 0,  # 滚轮上
            "scroll_down": 0,  # 滚轮下
        }
        self.start_time = time.time()
        self.last_save_time = time.time()

        # 创建界面
        self.create_widgets()

        # 绑定键盘事件
        keyboard.on_press(self.on_key_press)

        # 启动鼠标监听器（后台线程）
        self.mouse_listener = mouse.Listener(
            on_click=self.on_mouse_click,
            on_scroll=self.on_mouse_scroll,  # 可选：可监听滚轮
        )
        self.mouse_listener.start()

        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 加载历史数据
        self.load_history()

        # 不再使用 threading，改用 after 循环，必须在所有变量初始化之后
        self.update_display()  # 启动定时更新

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)  # 主内容区域可扩展

        # 标题（跨两列）
        title_label = ttk.Label(
            main_frame, text="键盘打字统计器", font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky=tk.N)

        # ========== 左侧区域 ==========
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(4, weight=1)  # 历史记录区域可扩展

        # 打字数量 & 时间
        self.count_label = ttk.Label(left_frame, text="打字数量: 0", font=("Arial", 14))
        self.count_label.grid(row=0, column=0, columnspan=2, pady=5, sticky=tk.W)

        self.time_label = ttk.Label(
            left_frame, text="运行时间: 00:00:00", font=("Arial", 12)
        )
        self.time_label.grid(row=1, column=0, columnspan=2, pady=(0, 10), sticky=tk.W)

        # 统计信息
        stats_frame = ttk.LabelFrame(left_frame, text="统计信息", padding="10")
        stats_frame.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        stats_frame.columnconfigure(0, weight=1)

        self.today_label = ttk.Label(
            stats_frame, text="今日打字数: 0", font=("Arial", 10)
        )
        self.today_label.grid(row=0, column=0, sticky=tk.W, pady=2)

        self.history_label = ttk.Label(
            stats_frame, text="历史总计: 0", font=("Arial", 10)
        )
        self.history_label.grid(row=1, column=0, sticky=tk.W, pady=2)

        # 按钮
        reset_btn = ttk.Button(left_frame, text="重置计数", command=self.reset_counter)
        reset_btn.grid(row=3, column=0, pady=10, padx=(0, 5), sticky=tk.W)

        save_btn = ttk.Button(left_frame, text="手动保存", command=self.save_data)
        save_btn.grid(row=3, column=1, pady=10, padx=(5, 0), sticky=tk.W)

        # 历史记录
        history_frame = ttk.LabelFrame(left_frame, text="历史记录", padding="10")
        history_frame.grid(
            row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5)
        )
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)

        columns = ("日期", "打字数")
        self.history_tree = ttk.Treeview(
            history_frame, columns=columns, show="headings", height=6
        )
        self.history_tree.heading("日期", text="日期")
        self.history_tree.heading("打字数", text="打字数")
        self.history_tree.column("日期", width=100, anchor=tk.CENTER)
        self.history_tree.column("打字数", width=80, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(
            history_frame, orient=tk.VERTICAL, command=self.history_tree.yview
        )
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        self.history_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 鼠标统计（放到历史记录下面）
        mouse_stats_frame = ttk.LabelFrame(
            left_frame, text="鼠标按键统计", padding="10"
        )
        mouse_stats_frame.grid(
            row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0)
        )
        mouse_stats_frame.columnconfigure(0, weight=1)

        mouse_columns = ("按键", "次数")
        self.mouse_tree = ttk.Treeview(
            mouse_stats_frame, columns=mouse_columns, show="headings", height=6
        )
        self.mouse_tree.heading("按键", text="按键")
        self.mouse_tree.heading("次数", text="次数")
        self.mouse_tree.column("按键", width=100, anchor=tk.CENTER)
        self.mouse_tree.column("次数", width=80, anchor=tk.CENTER)
        self.mouse_tree.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # ========== 右侧区域：仅按键统计（Top 26）==========
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)

        key_stats_frame = ttk.LabelFrame(
            right_frame, text="按键统计（Top 26）", padding="10"
        )
        key_stats_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        key_stats_frame.columnconfigure(0, weight=1)
        key_stats_frame.rowconfigure(0, weight=1)

        key_columns = ("按键", "次数", "占比")
        self.key_tree = ttk.Treeview(
            key_stats_frame, columns=key_columns, show="headings", height=15
        )  # 增加高度
        self.key_tree.heading("按键", text="按键")
        self.key_tree.heading("次数", text="次数")
        self.key_tree.heading("占比", text="占比")
        self.key_tree.column("按键", width=60, anchor=tk.CENTER)
        self.key_tree.column("次数", width=60, anchor=tk.CENTER)
        self.key_tree.column("占比", width=60, anchor=tk.CENTER)

        key_scrollbar = ttk.Scrollbar(
            key_stats_frame, orient=tk.VERTICAL, command=self.key_tree.yview
        )
        self.key_tree.configure(yscrollcommand=key_scrollbar.set)
        self.key_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        key_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 根窗口权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def on_key_press(self, event):
        # 不想忽略
        ## 忽略修饰键（如Ctrl, Alt, Shift等）
        # ignored_keys = [
        #     "ctrl",
        #     "alt",
        #     "shift",
        #     "caps lock",
        #     "tab",
        #     "esc",
        #     "enter",
        #     "backspace",
        #     "delete",
        #     "home",
        #     "end",
        #     "page up",
        #     "page down",
        #     "insert",
        #     "menu",
        #     "up",
        #     "down",
        #     "left",
        #     "right",
        #     "windows",
        # ]

        # if event.name.lower() not in ignored_keys:
        #     self.typing_count += 1
        key_name = event.name.lower()
        self.typing_count += 1
        # ← 新增：统计每个按键
        self.key_count[key_name] = self.key_count.get(key_name, 0) + 1

    def update_key_display(self):
        # 清空现有记录
        for item in self.key_tree.get_children():
            self.key_tree.delete(item)

        if self.typing_count == 0:
            return  # 避免除零

    def update_mouse_display(self):
        # 清空
        for item in self.mouse_tree.get_children():
            self.mouse_tree.delete(item)
        for item in self.mouse_tree.get_children():
            self.mouse_tree.delete(item)

        mapping = {
            "left": "鼠标左键",
            "right": "鼠标右键",
            "back": "后退键",
            "forward": "前进键",
            "scroll_up": "滚轮向上",
            "scroll_down": "滚轮向下",
        }
        for key, name in mapping.items():
            count = self.mouse_count.get(key, 0)
            self.mouse_tree.insert("", "end", values=(name, count))

        # 按次数排序，取前26
        sorted_keys = sorted(self.key_count.items(), key=lambda x: x[1], reverse=True)[
            :26
        ]

        for key_name, count in sorted_keys:
            percentage = (count / self.typing_count) * 100
            self.key_tree.insert(
                "", "end", values=(key_name, count, f"{percentage:.1f}%")
            )

    def update_display(self):
        # 更新打字计数显示（安全地在主线程中调用）
        self.count_label.config(text=f"打字数量: {self.typing_count}")

        # 更新运行时间
        elapsed_time = int(time.time() - self.start_time)
        hours = elapsed_time // 3600
        minutes = (elapsed_time % 3600) // 60
        seconds = elapsed_time % 60
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.time_label.config(text=f"运行时间: {time_str}")

        # 更新按键，鼠标统计显示
        self.update_key_display()
        self.update_mouse_display()

        # 每5秒自动保存一次
        if time.time() - self.last_save_time >= 5:
            self.save_data()

        # 使用 after 调度下一次更新（100毫秒后），形成循环
        self.root.after(100, self.update_display)  # 关键：在主线程中递归调用

    def reset_counter(self):
        # 重置时也要重置 saved_session_count
        self.typing_count = 0
        self.saved_session_count = 0
        self.key_count = {}  # 清空按键统计
        self.start_time = time.time()
        messagebox.showinfo("重置", "打字计数已重置！")

    def on_closing(self):
        self.save_data()  # 保存剩余未保存的数据
        # 停止鼠标监听器
        if hasattr(self, "mouse_listener"):
            self.mouse_listener.stop()
        self.root.destroy()

    def save_data(self):
        # 计算本次运行中新增但尚未保存的打字数
        unsaved_count = self.typing_count - self.saved_session_count

        if unsaved_count <= 0:
            return  # 没有新增数据，无需保存

        today = datetime.now().strftime("%Y-%m-%d")
        data = self.load_data_file()

        # 更新今日数据
        if today in data["daily_counts"]:
            data["daily_counts"][today] += unsaved_count
        else:
            data["daily_counts"][today] = unsaved_count

        # 更新历史总计
        data["total_count"] += unsaved_count

        # 更新已保存的会话计数
        self.saved_session_count = self.typing_count

        # 保存到文件
        with open("typing_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 更新界面中的今日和历史统计
        self.load_history()  # 或单独更新两个label也可以

        self.last_save_time = time.time()

    def load_data_file(self):
        try:
            with open("typing_data.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"daily_counts": {}, "total_count": 0}

    def load_history(self):
        data = self.load_data_file()

        # 更新今日统计
        today = datetime.now().strftime("%Y-%m-%d")
        today_count = data["daily_counts"].get(today, 0)
        self.today_label.config(text=f"今日打字数: {today_count}")

        # 更新历史总计
        total_count = data["total_count"]
        self.history_label.config(text=f"历史总计: {total_count}")

        # 更新历史记录显示
        self.update_history_display()

    def update_history_display(self):
        # 清空现有记录
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        # 加载数据并插入到Treeview
        data = self.load_data_file()
        sorted_dates = sorted(data["daily_counts"].keys(), reverse=True)

        for date in sorted_dates[:10]:  # 只显示最近10天
            count = data["daily_counts"][date]
            self.history_tree.insert("", "end", values=(date, count))

    def on_mouse_click(self, x, y, button, pressed):
        """鼠标点击回调（pressed=True 表示按下）"""
        if not pressed:  # 只统计“按下”动作，避免双计（按+松）
            return

        try:
            if button == mouse.Button.left:
                self.mouse_count["left"] += 1
            elif button == mouse.Button.right:
                self.mouse_count["right"] += 1
            elif button == mouse.Button.x1:  # 通常为“后退”键
                self.mouse_count["back"] += 1
            elif button == mouse.Button.x2:  # 通常为“前进”键
                self.mouse_count["forward"] += 1
        except AttributeError:
            # 某些系统可能不支持 x1/x2，忽略
            pass

    def on_mouse_scroll(self, x, y, dx, dy):
        """
        鼠标滚轮回调
        - dx: 水平滚动（通常为0，除非支持横向滚轮）
        - dy: 垂直滚动，>0 表示向上滚动，<0 表示向下滚动
        """
        if dy > 0:
            self.mouse_count["scroll_up"] += 1
        elif dy < 0:
            self.mouse_count["scroll_down"] += 1
        # 注意：一次滚动可能触发多个单位（如 dy=3），但通常我们只关心“滚动动作”次数，
        # 所以这里每次回调只 +1（即一次滚动事件算一次，不管滚多远）
        # 如果你想统计“滚动单位数”，可改为：self.mouse_count['scroll_up'] += dy


def main():
    root = tk.Tk()
    app = TypingCounterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
