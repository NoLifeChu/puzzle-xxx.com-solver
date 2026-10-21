import tkinter as tk
from itertools import product

def show_word_search(size, grid, target):
    """
    单词寻找 (Word Search) 交互式荧光笔可视化窗口:
    - size: 正方形尺寸 N
    - grid: 字符矩阵 [N][N]
    - target: 字典 {'WORD': ((r, c), (dr, dc), length), ...}
    """
    root = tk.Tk()
    root.title(f"Word Search Interactive Visualizer ({size}x{size})")
    root.geometry("1000x820")
    root.configure(bg="#1E1E28")

    # 根据尺寸自适应格子大小 (5x5 时约 70px, 20x20 时约 35px)
    cell_size = max(24, min(75, 700 // size))
    canvas_w = size * cell_size
    canvas_h = size * cell_size

    # 左侧：棋盘画布容器
    left_frame = tk.Frame(root, bg="#1E1E28", padx=15, pady=15)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH)

    canvas = tk.Canvas(left_frame, width=canvas_w, height=canvas_h, bg="#FFFFFF", highlightthickness=0)
    canvas.pack()

    # 右侧：单词点播台交互侧边栏
    right_frame = tk.Frame(root, bg="#2A2A38", padx=15, pady=15, width=280)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    title_label = tk.Label(right_frame, text="🎯 单词点播台", font=("Arial", 14, "bold"), bg="#2A2A38", fg="#FFE600")
    title_label.pack(anchor="w", pady=(0, 10))

    info_var = tk.StringVar(value="提示：点击下方单词可单独高亮！")
    info_label = tk.Label(right_frame, textvariable=info_var, font=("Consolas", 10), bg="#2A2A38", fg="#A0A0B8", wraplength=250, justify=tk.LEFT)
    info_label.pack(anchor="w", pady=(0, 10))

    # 荧光高亮配色池 (柔和明亮马卡龙色)
    PALETTE = [
        "#FFE066", "#70D6FF", "#FF70A6", "#99E2B4", "#FF9770",
        "#DDA0DD", "#80ED99", "#A0C4FF", "#FDFFB6", "#FFB5A7"
    ]

    word_list = list(target.keys())
    word_colors = {w: PALETTE[idx % len(PALETTE)] for idx, w in enumerate(word_list)}

    # 当前选中的单个单词（None 表示显示全部）
    current_selected = [None]

    def get_center(r, c):
        return c * cell_size + cell_size / 2, r * cell_size + cell_size / 2

    # 方向向量到中文名称的映射
    DIR_NAME = {
        (0, 1): "向右 →", (0, -1): "向左 ←", (1, 0): "向下 ↓", (-1, 0): "向上 ↑",
        (1, 1): "右下 ↘", (-1, 1): "右上 ↗", (1, -1): "左下 ↙", (-1, -1): "左上 ↖"
    }

    # 核心绘图函数
    def draw():
        canvas.delete("all")
        cs = cell_size

        # 1. 绘制底层棋盘方格
        for r in range(size):
            for c in range(size):
                x1, y1 = c * cs, r * cs
                x2, y2 = x1 + cs, y1 + cs
                canvas.create_rectangle(x1, y1, x2, y2, fill="#FFFFFF", outline="#E8E8EE", width=1)

        # 2. 绘制荧光笔划线标记 (绘制在文字下方，不挡字母)
        line_w = int(cs * 0.76)
        active_word = current_selected[0]

        for w, spec in target.items():
            if not spec or len(spec) < 3:
                continue # 尚未求解出的单词跳过
            
            # 如果处于“单词点播状态”，只画当前选中的单词！
            if active_word is not None and w != active_word:
                continue

            (r0, c0), (dr, dc), length = spec
            end_r = r0 + (length - 1) * dr
            end_c = c0 + (length - 1) * dc

            x1, y1 = get_center(r0, c0)
            x2, y2 = get_center(end_r, end_c)

            color = word_colors.get(w, "#FFE066") if active_word is None else "#FF3366"

            # 绘制荧光胶囊线段
            canvas.create_line(x1, y1, x2, y2, width=line_w, fill=color, capstyle=tk.ROUND)

        # 3. 绘制字母 (置于顶层，保证绝对清晰！)
        font_size = max(9, int(cs * 0.44))
        font_style = ("Consolas", font_size, "bold")

        for r in range(size):
            for c in range(size):
                cx, cy = get_center(r, c)
                letter = grid[r][c]
                canvas.create_text(cx, cy, text=str(letter), fill="#1A1A24", font=font_style)

        # 外围细边框
        canvas.create_rectangle(1, 1, canvas_w, canvas_h, outline="#CCCCCC", width=2)

    # 交互控制：点击单词高亮
    def select_word(word):
        current_selected[0] = word
        spec = target.get(word, None)
        if spec and len(spec) >= 3:
            (r0, c0), (dr, dc), length = spec
            d_str = DIR_NAME.get((dr, dc), f"({dr},{dc})")
            info_var.set(f"已选中: {word}\n起点: 行{r0+1}, 列{c0+1}\n方向: {d_str} | 长度: {length}")
        else:
            info_var.set(f"已选中: {word} (未找到答案)")
        draw()

    def show_all():
        current_selected[0] = None
        info_var.set("当前状态: 显示全部已找出的单词")
        draw()

    # 顶置“显示全部”按钮
    btn_all = tk.Button(right_frame, text="🌈 显示全部 (Show All)", font=("Arial", 10, "bold"), bg="#3E3E52", fg="#FFFFFF", relief=tk.FLAT, command=show_all)
    btn_all.pack(fill=tk.X, pady=(0, 10))

    # 单词列表滚动区域
    listbox_frame = tk.Frame(right_frame, bg="#2A2A38")
    listbox_frame.pack(fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
    listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, font=("Consolas", 12, "bold"), bg="#1E1E28", fg="#E2E2F0", selectbackground="#4A90E2", selectforeground="#FFFFFF", relief=tk.FLAT, borderwidth=0)
    scrollbar.config(command=listbox.yview)

    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    for w in word_list:
        listbox.insert(tk.END, f"  {w}")

    def on_listbox_select(event):
        sel = listbox.curselection()
        if sel:
            idx = sel[0]
            select_word(word_list[idx])

    listbox.bind("<<ListboxSelect>>", on_listbox_select)

    draw()
    root.mainloop()

size = 20
grid = [["W","G","C","N","O","T","H","I","N","G","N","E","S","S","H","H","V","F","B","E"],["Z","N","O","Y","M","I","Z","A","M","O","U","J","L","S","G","D","N","I","X","T"],["L","D","F","H","D","U","M","U","I","Y","S","T","E","R","E","O","B","M","T","M"],["E","B","I","E","C","E","A","T","T","E","S","T","E","D","I","L","K","G","A","S"],["L","M","O","S","L","I","C","O","N","S","E","C","U","T","I","V","E","L","Y","Y"],["Q","U","X","D","Q","E","C","O","D","M","I","C","A","O","T","K","L","R","T","Q"],["T","E","D","D","R","U","H","P","N","A","R","C","G","R","G","X","X","I","I","B"],["Y","I","H","I","O","T","A","O","S","T","I","R","I","E","E","U","L","R","E","W"],["M","S","D","S","T","T","R","L","E","F","A","D","G","L","E","I","A","E","N","X"],["P","E","O","G","A","O","A","A","I","P","D","M","N","A","B","K","Y","S","E","K"],["R","V","L","R","R","U","C","R","H","F","D","X","I","A","T","U","U","P","G","H"],["U","I","P","U","A","U","T","I","W","M","Y","M","L","N","M","R","P","I","O","I"],["R","T","H","N","P","C","E","S","Y","L","A","I","K","G","A","B","A","R","M","H"],["P","A","I","T","E","S","R","A","T","T","A","I","N","E","D","T","O","A","O","S"],["C","R","N","L","S","B","I","T","F","V","R","L","I","G","R","S","I","T","H","P"],["H","E","E","E","I","O","S","I","A","D","H","X","W","G","C","R","B","O","G","K"],["I","P","C","D","R","Z","T","O","S","S","O","V","T","O","M","K","W","R","N","A"],["N","M","L","O","G","B","I","N","C","Q","I","B","P","J","V","M","I","O","R","X"],["G","I","T","R","E","B","C","N","P","D","Y","E","C","Q","A","S","W","S","N","Q"],["L","A","S","E","Z","M","U","E","G","A","S","I","V","N","E","S","I","L","G","T"]]
target = {"ATTAINED":[],"ATTESTED":[],"BIBLIOGRAPHIES":[],"BIOAVAILABILITY":[],"CHARACTERISTIC":[],"CONSECUTIVE":[],"CONSECUTIVELY":[],"DECONTAMINATION":[],"DIRT":[],"DISGRUNTLED":[],"DISQUALIFYING":[],"DOLPHIN":[],"ELECTRIFICATION":[],"ENVISAGE":[],"GEEK":[],"HIDEOUT":[],"HOMOGENEITY":[],"HOROSCOPES":[],"IMPERATIVES":[],"KNOWS":[],"LAYUP":[],"MANDI":[],"MICA":[],"MIDDLEMAN":[],"NARC":[],"NODE":[],"NOTHINGNESS":[],"POLARISATION":[],"PUBLICIST":[],"REDIRECTION":[],"RESPIRATOR":[],"SCARE":[],"SEPARATOR":[],"SHOWMAN":[],"STEREO":[],"TAOS":[],"TEACUP":[],"TWINKLING":[],"UTILIZING":[],"WIRELESS":[]}

#史上最简单的求解器，给出两个等价版本，恰好都是12行；运行时使用其中一个即可
#递归版
def digui(word,v,i,j,l):
    if l==len(word):
        return True
    if 0<=i<size and 0<=j<size and grid[i][j]==word[l]:#仔细看能看到短路求值
        return digui(word,v,i+v[0],j+v[1],l+1)
    return False
vector=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
for word in target:#解这个单词
    for i, j in product(range(size), range(size)):#扫描每个格子周围
        for v in vector:
            if digui(word,v,i,j,0):
                target[word]=((i,j),v,len(word))#若某单词有多个答案，会全部找出，但只有最后一个保存

#循环版
vector=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
for word in target:#解这个单词
    for i, j in product(range(size), range(size)):#扫描每个格子周围
        for v in vector:
            di,dj=i,j
            for l in range(len(word)):
                if 0<=di<size and 0<=dj<size and grid[di][dj]==word[l]:#仔细看能看到短路求值
                    di,dj=di+v[0],dj+v[1]
                else:
                    break
            else:
                target[word]=((i,j),v,len(word))#若某单词有多个答案，会全部找出，但只有最后一个保存

show_word_search(size, grid, target)
