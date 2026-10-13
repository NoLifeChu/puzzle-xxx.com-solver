from playwright.sync_api import sync_playwright
import tkinter as tk

from playwright.sync_api import sync_playwright

def fetch_binairo_plus(url="https://www.puzzle-binairo.com/"):
    """
    全自动后台静默抓取黑白+（支持每日 24x24、每月 30x40 等任意尺寸）
    返回格式:
        width: 宽度
        height: 高度
        grid: height * width 二维矩阵 (1黑, 0白, -1未知)
        same_pairs: 相等关系元组列表 [((r1, c1), (r2, c2)), ...]
        diff_pairs: 不等关系元组列表 [((r1, c1), (r2, c2)), ...]
    """
    print(f"正在后台启动无头浏览器抓取黑白+题目: {url} ...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        # 核心等待：等棋盘所有格子加载就位
        page.wait_for_selector('div[tabindex="-1"]')

        # 注入实测验证成功的像素对齐脚本
        data = page.evaluate("""() => {
            let cells = Array.from(document.querySelectorAll('div[tabindex="-1"]')).filter(c => 
                c.classList.contains('cell') || c.classList.contains('task-cell')
            );

            cells.sort((a, b) => a.offsetTop - b.offsetTop || a.offsetLeft - b.offsetLeft);

            let rowsMap = new Map();
            cells.forEach(c => {
                let top = c.offsetTop;
                let foundKey = null;
                for (let k of rowsMap.keys()) {
                    if (Math.abs(k - top) < 5) { foundKey = k; break; }
                }
                if (foundKey === null) { foundKey = top; rowsMap.set(foundKey, []); }
                rowsMap.get(foundKey).push(c);
            });

            let sortedRowTops = Array.from(rowsMap.keys()).sort((a, b) => a - b);
            let height = sortedRowTops.length;
            let width = rowsMap.get(sortedRowTops[0]).length;

            let firstRow = rowsMap.get(sortedRowTops[0]);
            firstRow.sort((a, b) => a.offsetLeft - b.offsetLeft);
            let sortedColLefts = firstRow.map(c => c.offsetLeft);

            let cell_h = sortedRowTops.length > 1 ? (sortedRowTops[1] - sortedRowTops[0]) : 35;
            let cell_w = sortedColLefts.length > 1 ? (sortedColLefts[1] - sortedColLefts[0]) : 35;

            // 1. 提取基础棋盘
            let grid = [];
            for (let topKey of sortedRowTops) {
                let rowCells = rowsMap.get(topKey);
                rowCells.sort((a, b) => a.offsetLeft - b.offsetLeft);
                let rowData = [];
                for (let c of rowCells) {
                    if (c.classList.contains('cell-1')) rowData.push(1);
                    else if (c.classList.contains('cell-0')) rowData.push(0);
                    else rowData.push(-1);
                }
                grid.push(rowData);
            }

            // 2. 提取修正后的线索对 (修正作者 h/v 分界线反转)
            let clues = Array.from(document.querySelectorAll('.comparison-clue'));
            let same_pairs = [];
            let diff_pairs = [];

            function findClosestIndex(arr, val) {
                let bestIdx = 0, minDiff = Infinity;
                for (let i = 0; i < arr.length; i++) {
                    let diff = Math.abs(arr[i] - val);
                    if (diff < minDiff) { minDiff = diff; bestIdx = i; }
                }
                return bestIdx;
            }

            clues.forEach(el => {
                let isEq = el.classList.contains('eqh') || el.classList.contains('eqv') || el.classList.contains('icon-eq');
                let isLeftRight = el.classList.contains('eqv') || el.classList.contains('nev');

                let top = el.offsetTop;
                let left = el.offsetLeft;

                if (isLeftRight) {
                    let r = findClosestIndex(sortedRowTops, top - cell_h / 2);
                    let rightCol = findClosestIndex(sortedColLefts, left);
                    let leftCol = rightCol - 1;

                    if (0 <= r && r < height && 0 <= leftCol && rightCol < width) {
                        let pair = [[r, leftCol], [r, rightCol]];
                        if (isEq) same_pairs.push(pair);
                        else diff_pairs.push(pair);
                    }
                } else {
                    let c = findClosestIndex(sortedColLefts, left - cell_w / 2);
                    let bottomRow = findClosestIndex(sortedRowTops, top);
                    let topRow = bottomRow - 1;

                    if (0 <= c && c < width && 0 <= topRow && bottomRow < height) {
                        let pair = [[topRow, c], [bottomRow, c]];
                        if (isEq) same_pairs.push(pair);
                        else diff_pairs.push(pair);
                    }
                }
            });

            return {
                width: width,
                height: height,
                grid: grid,
                same_pairs: same_pairs,
                diff_pairs: diff_pairs
            };
        }""")

        browser.close()
        
        # 将 JS 的嵌套数组转换为 Python 原生元组格式 [((r1, c1), (r2, c2)), ...]
        same_pairs = [((p[0][0], p[0][1]), (p[1][0], p[1][1])) for p in data["same_pairs"]]
        diff_pairs = [((p[0][0], p[0][1]), (p[1][0], p[1][1])) for p in data["diff_pairs"]]

        print(f"✔ 黑白+ 全自动抓取成功！尺寸: 宽 {data['width']} x 高 {data['height']}")
        print(f"  相等符号(=): {len(same_pairs)} 个 | 不等符号(×): {len(diff_pairs)} 个")
        
        return data["width"], data["height"], data["grid"], same_pairs, diff_pairs

def show_binairo(grid, same_pairs=None, diff_pairs=None):
    """
    黑白/黑白+ 高级诊断雷达 (带行列号、剩余额度仪表盘、自由缩放与滚动)
    """
    if same_pairs is None: same_pairs = []
    if diff_pairs is None: diff_pairs = []

    height = len(grid)
    width = len(grid[0])

    root = tk.Tk()
    title_suffix = " (Binairo+)" if (same_pairs or diff_pairs) else " (Binairo)"
    root.title(f"Binairo Radar ({width}x{height}){title_suffix}")
    root.geometry("1000x850")

    # 1. 初始格子尺寸自适应
    cell_size = [max(18, min(32, 700 // max(height, width)))]

    # 2. 预先计算每行、每列剩余的黑/白额度
    target_b_row = width // 2
    target_w_row = width // 2
    target_b_col = height // 2
    target_w_col = height // 2

    # 顶部控制面板 (缩放按钮)
    top_bar = tk.Frame(root, bg="#2A2A36", pady=6)
    top_bar.pack(fill=tk.X)

    zoom_label = tk.Label(top_bar, text=f"格子大小: {cell_size[0]}px", bg="#2A2A36", fg="#FFFFFF", font=("Arial", 10, "bold"))
    zoom_label.pack(side=tk.LEFT, padx=15)

    # 滚动区域框架
    frame = tk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)

    h_scroll = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
    v_scroll = tk.Scrollbar(frame, orient=tk.VERTICAL)
    canvas = tk.Canvas(frame, bg="#DDD8F0", xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

    h_scroll.config(command=canvas.xview)
    v_scroll.config(command=canvas.yview)

    h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
    v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def draw():
        canvas.delete("all")
        cs = cell_size[0]

        # 边距留白参数
        m_left = max(35, int(cs * 1.5))    # 放行号 1~H
        m_top = max(28, int(cs * 1.2))     # 放列号 1~W
        m_right = max(65, int(cs * 2.8))   # 放右侧行剩余黑|白
        m_bottom = max(38, int(cs * 1.6))  # 放底部列剩余黑|白

        total_w = m_left + width * cs + m_right
        total_h = m_top + height * cs + m_bottom

        canvas.config(scrollregion=(0, 0, total_w, total_h))
        zoom_label.config(text=f"格子大小: {cs}px (全盘: {width}x{height})")

        # 字体
        idx_font = ("Arial", max(7, int(cs * 0.35)), "bold")
        info_font = ("Consolas", max(7, int(cs * 0.38)), "bold")
        symbol_font = ("Arial", max(8, int(cs * 0.42)), "bold")

        # A. 绘制顶部列号与底部剩余额度
        for c in range(width):
            cx = m_left + c * cs + cs / 2
            # 顶部列号
            canvas.create_text(cx, m_top / 2, text=str(c + 1), fill="#5A527A", font=idx_font)

            # 统计这一列
            col_vals = [grid[r][c] for r in range(height)]
            b_cnt = col_vals.count(1)
            w_cnt = col_vals.count(0)
            rem_b = target_b_col - b_cnt
            rem_w = target_w_col - w_cnt

            by = m_top + height * cs + m_bottom / 2
            if rem_b == 0 and rem_w == 0:
                canvas.create_text(cx, by, text="✔", fill="#2E7D32", font=info_font)
            elif rem_b < 0 or rem_w < 0:
                canvas.create_text(cx, by, text="ERR", fill="#D32F2F", font=info_font)
            else:
                canvas.create_text(cx, by, text=f"{rem_b}|{rem_w}", fill="#3F3859", font=info_font)

        # B. 绘制左侧行号与右侧剩余额度
        for r in range(height):
            cy = m_top + r * cs + cs / 2
            # 左侧行号
            canvas.create_text(m_left / 2, cy, text=str(r + 1), fill="#5A527A", font=idx_font)

            # 统计这一行
            row_vals = grid[r]
            b_cnt = row_vals.count(1)
            w_cnt = row_vals.count(0)
            rem_b = target_b_row - b_cnt
            rem_w = target_w_row - w_cnt

            rx = m_left + width * cs + m_right / 2
            if rem_b == 0 and rem_w == 0:
                canvas.create_text(rx, cy, text="✔", fill="#2E7D32", font=info_font)
            elif rem_b < 0 or rem_w < 0:
                canvas.create_text(rx, cy, text="ERR", fill="#D32F2F", font=info_font)
            else:
                canvas.create_text(rx, cy, text=f"{rem_b}|{rem_w}", fill="#3F3859", font=info_font)

        # C. 绘制网格线与棋子
        r_pad = cs * 0.36
        outline_w = max(1, int(cs * 0.08))

        for r in range(height):
            for c in range(width):
                x1 = m_left + c * cs
                y1 = m_top + r * cs
                x2 = x1 + cs
                y2 = y1 + cs

                # 底格
                canvas.create_rectangle(x1, y1, x2, y2, fill="#DDD8F0", outline="#B8B0D4", width=1)

                val = grid[r][c]
                cx = x1 + cs / 2
                cy = y1 + cs / 2

                if val == 1:
                    canvas.create_oval(cx - r_pad, cy - r_pad, cx + r_pad, cy + r_pad, fill="#1A1A1E", outline="#1A1A1E")
                elif val == 0:
                    canvas.create_oval(cx - r_pad, cy - r_pad, cx + r_pad, cy + r_pad, fill="#FFFFFF", outline="#1A1A1E", width=outline_w)

        # D. 绘制比较线索 = 和 x
        badge_r = max(4, int(cs * 0.22))
        def draw_clue_badge(p1, p2, txt, color):
            (r1, c1), (r2, c2) = p1, p2
            if r1 == r2: # 水平
                mid_x = m_left + max(c1, c2) * cs
                mid_y = m_top + r1 * cs + cs / 2
            else: # 垂直
                mid_x = m_left + c1 * cs + cs / 2
                mid_y = m_top + max(r1, r2) * cs
            canvas.create_oval(mid_x - badge_r, mid_y - badge_r, mid_x + badge_r, mid_y + badge_r, fill="#DDD8F0", outline="")
            canvas.create_text(mid_x, mid_y, text=txt, fill=color, font=symbol_font)

        for pair in same_pairs:
            draw_clue_badge(pair[0], pair[1], "=", "#3B3561")
        for pair in diff_pairs:
            draw_clue_badge(pair[0], pair[1], "×", "#993333")

    # 缩放控制器
    def zoom(delta):
        new_size = cell_size[0] + delta
        if 14 <= new_size <= 65:
            cell_size[0] = new_size
            draw()

    # 绑定快捷键与控制按钮
    btn_zoom_in = tk.Button(top_bar, text=" 放大 (+) ", bg="#3F3F50", fg="#FFF", relief=tk.FLAT, command=lambda: zoom(4))
    btn_zoom_in.pack(side=tk.LEFT, padx=5)

    btn_zoom_out = tk.Button(top_bar, text=" 缩小 (-) ", bg="#3F3F50", fg="#FFF", relief=tk.FLAT, command=lambda: zoom(-4))
    btn_zoom_out.pack(side=tk.LEFT, padx=5)

    btn_reset = tk.Button(top_bar, text=" 重置 ", bg="#3F3F50", fg="#FFF", relief=tk.FLAT, command=lambda: (cell_size.__setitem__(0, max(18, min(32, 700 // max(height, width)))), draw()))
    btn_reset.pack(side=tk.LEFT, padx=5)

    # 鼠标滚轮缩放绑定 (Ctrl + 滚轮)
    def on_mouse_wheel(event):
        if event.state & 0x0004: # Ctrl 按下
            if event.delta > 0 or event.num == 4: zoom(2)
            else: zoom(-2)

    root.bind("<MouseWheel>", on_mouse_wheel)
    root.bind("<Button-4>", on_mouse_wheel)
    root.bind("<Button-5>", on_mouse_wheel)

    draw()
    root.mainloop()

def chick_near(x,y,xy,location):#鸡近
    smalllist=[]#至少这真是个列表，反观……
    for a in range(3):
        smalllist.append((x+xy*(location+a),y+(1-xy)*(location+a)))
    for a in smalllist:
        if a[0]<0 or a[0]>=height or a[1]<0 or a[1]>=width:
            return 0
    smalllist.remove((x,y))
    answer=grid[smalllist[0][0]][smalllist[0][1]]
    if answer == grid[smalllist[1][0]][smalllist[1][1]] and answer!=-1:
        grid[x][y]=1-answer
        return 1
    else:
        return 0

def analysis(subject,xy,location):#这次用数对的思想处理
    #0.计算缺口
    gap=[int(len(subject)/2)]*2
    for i in subject:
        if i != -1:
            gap[i]-=1
    #1.提取空当
    space=[a for a in range(len(subject)) if subject[a]==-1]
    #2.去除数对
    pairs=[]
    for i in cancal_actual_pairs:
        if i[0][xy]==i[1][xy] and i[0][xy]==location:
            if i[0][1-xy] in space and i[1][1-xy] in space:
                pairs.append((i[0][1-xy],i[1][1-xy]))
                space.remove(i[0][1-xy])
                space.remove(i[1][1-xy])

    #3.黑白分别处理
    black_pairs=pairs[:]
    white_pairs=pairs[:]
    pointer=0
    while pointer<len(space)-1:#特化加入
        if space[pointer+1]-space[pointer]==1:
            neigh=[-1,-1]
            if space[pointer]>0:
                neigh[0]=subject[space[pointer]-1]
            if space[pointer+1]<len(subject)-1:
                neigh[1]=subject[space[pointer+1]+1]
            if neigh!=[-1,-1]:
                if 0 in neigh:
                    black_occupied=[]
                    for i in black_pairs:
                        for j in i:
                            black_occupied.append(j)
                    if space[pointer] not in black_occupied:
                        black_pairs.append((space[pointer],space[pointer+1]))
                if 1 in neigh:
                    white_occupied=[]
                    for i in white_pairs:
                        for j in i:
                            white_occupied.append(j)
                    if space[pointer] not in white_occupied:
                        white_pairs.append((space[pointer],space[pointer+1]))

        elif space[pointer+1]-space[pointer]==2:
            neigh=subject[space[pointer]+1]
            if neigh==0:
                black_occupied=[]
                for i in black_pairs:
                    for j in i:
                        black_occupied.append(j)
                if space[pointer] not in black_occupied:
                    black_pairs.append((space[pointer],space[pointer+1]))
            if neigh==1:
                white_occupied=[]
                for i in white_pairs:
                    for j in i:
                        white_occupied.append(j)
                if space[pointer] not in white_occupied:
                    white_pairs.append((space[pointer],space[pointer+1]))
        pointer+=1
    pointer=0
    while pointer<len(space)-2: #通用加入
        if space[pointer+2]-space[pointer]==2:
            white_occupied=[]
            for i in white_pairs:
                for j in i:
                    white_occupied.append(j)
            black_occupied=[]
            for i in black_pairs:
                for j in i:
                    black_occupied.append(j)
            if set((space[pointer],space[pointer+1],space[pointer+2]))&set(white_occupied) == set():
                white_pairs.append((space[pointer],space[pointer+1],space[pointer+2]))
            if set((space[pointer],space[pointer+1],space[pointer+2]))&set(black_occupied) == set():
                black_pairs.append((space[pointer],space[pointer+1],space[pointer+2]))
        pointer+=1
    #4.请输入文本
    result=[]
    if len(white_pairs)==gap[0]:
        occupied=[]
        for i in white_pairs:
            for j in i:
                occupied.append(j)
        real=set(space)-set(occupied)
        for i in real:
            result.append((i,1))
    if len(black_pairs)==gap[1]:
        occupied=[]
        for i in black_pairs:
            for j in i:
                occupied.append(j)
        real=set(space)-set(occupied)
        for i in real:
            result.append((i,0))
    return result

#自动
#width, height, grid, same_pairs, diff_pairs = fetch_binairo_plus("https://cn.puzzle-binairo.com/monthly-binairo-plus/")

#手动
width = 30
height = 40
grid = [[-1,1,-1,-1,-1,1,-1,-1,-1,-1,-1,-1,1,-1,-1,-1,-1,1,-1,-1,-1,-1,-1,-1,1,-1,-1,-1,1,-1],[0,1,0,-1,-1,-1,-1,1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,0,-1,-1,-1,-1,1,1,0],[-1,-1,1,-1,0,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,1,-1,0,-1,-1],[-1,-1,-1,0,-1,-1,-1,-1,-1,-1,-1,-1,0,-1,1,0,-1,1,-1,-1,-1,-1,-1,-1,-1,-1,0,-1,-1,-1],[1,-1,-1,1,-1,-1,-1,-1,-1,0,-1,-1,1,0,-1,-1,1,0,-1,-1,1,-1,-1,-1,-1,-1,0,-1,-1,0],[-1,0,-1,-1,-1,-1,0,-1,0,-1,-1,1,-1,-1,-1,-1,-1,-1,1,-1,-1,1,-1,0,-1,-1,-1,-1,1,-1],[-1,-1,-1,-1,0,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,0,-1,-1,-1,-1],[0,-1,-1,-1,0,0,-1,-1,-1,-1,-1,-1,-1,-1,1,1,-1,-1,-1,-1,-1,-1,-1,-1,1,1,-1,-1,-1,0],[0,-1,-1,-1,-1,-1,0,-1,-1,-1,1,-1,-1,-1,-1,-1,-1,-1,-1,1,-1,-1,-1,1,-1,-1,-1,-1,-1,0],[1,-1,-1,-1,-1,-1,-1,-1,-1,-1,1,0,-1,-1,0,1,-1,-1,1,1,-1,-1,-1,-1,-1,-1,-1,-1,-1,1],[-1,-1,-1,-1,-1,0,0,-1,-1,-1,-1,1,-1,-1,1,0,-1,-1,1,-1,-1,-1,-1,0,1,-1,-1,-1,-1,-1],[-1,-1,-1,-1,-1,-1,1,-1,-1,1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,1,-1,-1,0,-1,-1,-1,-1,-1,-1],[-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,1,-1,-1,-1,-1,-1,-1,1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1],[-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1],[-1,-1,-1,-1,-1,-1,-1,-1,0,-1,-1,-1,-1,-1,1,0,-1,-1,-1,-1,-1,0,-1,-1,-1,-1,-1,-1,-1,-1],[-1,0,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,0,-1,-1,-1,-1,1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,1,-1],[-1,-1,-1,-1,-1,-1,-1,-1,-1,0,1,0,-1,1,-1,-1,1,-1,0,1,1,-1,-1,-1,-1,-1,-1,-1,-1,-1],[-1,-1,-1,-1,-1,-1,-1,1,-1,-1,-1,-1,-1,-1,1,1,-1,-1,-1,-1,-1,-1,0,-1,-1,-1,-1,-1,-1,-1],[-1,-1,-1,-1,-1,0,-1,-1,-1,-1,-1,0,-1,-1,-1,-1,-1,-1,1,-1,-1,-1,-1,-1,1,-1,-1,-1,-1,-1],[-1,-1,-1,1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,1,-1,-1,-1],[-1,-1,0,-1,-1,0,-1,-1,-1,0,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,1,-1,-1,-1,0,-1,-1,1,-1,-1],[0,-1,-1,-1,-1,-1,1,-1,0,-1,-1,-1,-1,1,-1,-1,1,-1,-1,-1,-1,1,-1,0,-1,-1,-1,-1,-1,1],[-1,-1,1,-1,-1,-1,-1,-1,-1,-1,0,1,0,-1,-1,-1,-1,1,1,0,-1,-1,-1,-1,-1,-1,-1,0,-1,-1],[1,-1,-1,-1,-1,-1,-1,-1,-1,1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,0,-1,-1,-1,-1,-1,-1,-1,-1,0],[-1,-1,-1,0,1,-1,-1,0,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,0,-1,-1,0,1,-1,-1,-1],[-1,-1,-1,-1,0,1,-1,0,-1,-1,-1,-1,0,-1,-1,-1,-1,0,-1,-1,-1,-1,1,-1,0,1,-1,-1,-1,-1],[-1,-1,-1,-1,-1,-1,-1,-1,-1,1,-1,-1,0,-1,-1,-1,-1,1,-1,-1,0,-1,-1,-1,-1,-1,-1,-1,-1,-1],[-1,-1,-1,-1,-1,-1,-1,-1,-1,0,-1,-1,1,1,0,0,1,1,-1,-1,1,-1,-1,-1,-1,-1,-1,-1,-1,-1],[-1,1,-1,1,-1,-1,0,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,1,-1,-1,0,-1,1,-1],[-1,-1,-1,0,-1,-1,-1,-1,-1,-1,-1,-1,-1,1,-1,-1,0,-1,-1,-1,-1,-1,-1,-1,-1,-1,0,-1,-1,-1],[-1,0,-1,-1,-1,-1,-1,-1,0,-1,-1,-1,0,-1,-1,-1,-1,1,-1,-1,-1,1,-1,-1,-1,-1,-1,-1,1,-1],[-1,-1,0,1,-1,-1,0,-1,-1,-1,-1,1,-1,-1,-1,-1,-1,-1,1,-1,-1,-1,-1,1,-1,-1,1,0,-1,-1],[-1,0,-1,-1,-1,0,-1,-1,-1,-1,-1,0,-1,-1,-1,-1,-1,-1,0,-1,-1,-1,-1,-1,1,-1,-1,-1,1,-1],[-1,0,1,-1,-1,-1,-1,-1,-1,-1,-1,-1,0,-1,-1,-1,-1,1,-1,-1,-1,-1,-1,-1,-1,-1,-1,1,0,-1],[-1,1,0,-1,-1,-1,-1,-1,-1,0,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,1,-1,-1,-1,-1,-1,-1,0,1,-1],[-1,-1,1,0,1,-1,1,-1,-1,1,-1,-1,-1,0,-1,-1,1,-1,-1,-1,0,-1,-1,1,-1,1,0,1,-1,-1],[1,0,0,1,0,-1,-1,-1,-1,0,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,1,-1,-1,-1,-1,0,1,0,0,1],[-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,1,-1,-1,1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1],[-1,1,1,-1,1,-1,1,-1,-1,-1,-1,-1,-1,-1,1,0,-1,-1,-1,-1,-1,-1,-1,0,-1,1,-1,1,0,-1],[-1,-1,0,-1,-1,-1,-1,-1,-1,-1,1,-1,-1,-1,-1,-1,-1,-1,-1,1,-1,-1,-1,-1,-1,-1,-1,1,-1,-1]]
same_pairs = (((0,9),(0,10)),((0,23),(1,23)),((0,25),(1,25)),((1,10),(1,11)),((1,15),(1,16)),((1,20),(2,20)),((2,1),(3,1)),((2,12),(2,13)),((2,28),(3,28)),((2,29),(3,29)),((4,15),(5,15)),((4,27),(4,28)),((6,7),(6,8)),((6,17),(6,18)),((7,2),(8,2)),((7,11),(7,12)),((7,26),(7,27)),((8,8),(8,9)),((8,12),(9,12)),((9,1),(9,2)),((10,12),(11,12)),((10,13),(11,13)),((12,27),(13,27)),((13,9),(14,9)),((13,10),(13,11)),((13,12),(14,12)),((13,17),(13,18)),((14,0),(15,0)),((14,5),(14,6)),((14,7),(15,7)),((14,22),(15,22)),((15,14),(15,15)),((15,21),(15,22)),((16,2),(16,3)),((16,24),(17,24)),((16,26),(17,26)),((17,1),(18,1)),((17,4),(17,5)),((17,11),(17,12)),((18,7),(18,8)),((18,20),(18,21)),((18,26),(18,27)),((19,6),(20,6)),((19,11),(20,11)),((20,18),(20,19)),((22,6),(23,6)),((22,16),(23,16)),((22,21),(22,22)),((22,23),(23,23)),((23,1),(23,2)),((23,5),(24,5)),((23,10),(24,10)),((23,18),(23,19)),((24,1),(24,2)),((24,14),(25,14)),((24,15),(25,15)),((24,19),(25,19)),((24,28),(24,29)),((25,0),(26,0)),((25,3),(26,3)),((26,0),(26,1)),((26,6),(26,7)),((26,19),(27,19)),((26,28),(27,28)),((27,26),(27,27)),((28,29),(29,29)),((29,2),(30,2)),((29,5),(29,6)),((29,19),(29,20)),((30,19),(31,19)),((32,6),(32,7)),((32,9),(33,9)),((32,19),(33,19)),((32,25),(33,25)),((33,0),(34,0)),((33,5),(33,6)),((33,9),(33,10)),((33,15),(34,15)),((34,21),(34,22)),((34,29),(35,29)),((35,18),(35,19)),((36,18),(37,18)),((36,22),(37,22)),((37,3),(38,3)),((37,9),(38,9)),((37,12),(38,12)),((37,23),(37,24)),((38,7),(39,7)),((38,20),(39,20)),((38,29),(39,29)),((39,13),(39,14)),((39,22),(39,23)),((39,24),(39,25)))
diff_pairs = (((0,6),(0,7)),((0,6),(1,6)),((0,16),(1,16)),((0,18),(1,18)),((1,9),(1,10)),((1,11),(1,12)),((1,18),(1,19)),((1,19),(1,20)),((1,23),(1,24)),((2,0),(3,0)),((2,20),(2,21)),((2,21),(2,22)),((2,22),(2,23)),((3,19),(3,20)),((4,7),(5,7)),((4,10),(5,10)),((5,14),(5,15)),((7,16),(8,16)),((7,18),(7,19)),((7,19),(7,20)),((7,22),(7,23)),((7,27),(8,27)),((8,7),(8,8)),((8,21),(9,21)),((9,1),(10,1)),((9,21),(10,21)),((9,23),(9,24)),((9,26),(10,26)),((10,2),(10,3)),((11,1),(11,2)),((11,11),(11,12)),((11,15),(12,15)),((11,17),(11,18)),((11,18),(11,19)),((11,28),(11,29)),((11,29),(12,29)),((12,0),(13,0)),((12,6),(12,7)),((12,15),(12,16)),((12,27),(12,28)),((12,28),(13,28)),((13,1),(14,1)),((13,3),(13,4)),((13,5),(14,5)),((13,10),(14,10)),((13,19),(13,20)),((13,20),(13,21)),((14,0),(14,1)),((14,16),(14,17)),((14,16),(15,16)),((14,28),(14,29)),((15,7),(15,8)),((16,6),(17,6)),((16,12),(17,12)),((16,29),(17,29)),((17,17),(17,18)),((18,0),(19,0)),((18,15),(19,15)),((18,16),(19,16)),((19,10),(19,11)),((19,16),(20,16)),((19,18),(19,19)),((19,23),(19,24)),((19,25),(20,25)),((20,3),(20,4)),((20,3),(21,3)),((20,4),(21,4)),((20,25),(21,25)),((21,2),(21,3)),((21,7),(22,7)),((21,9),(21,10)),((22,20),(22,21)),((22,28),(23,28)),((23,28),(24,28)),((25,10),(26,10)),((26,6),(27,6)),((26,29),(27,29)),((28,8),(29,8)),((28,9),(28,10)),((28,9),(29,9)),((28,19),(29,19)),((29,15),(30,15)),((29,21),(29,22)),((30,9),(30,10)),((30,10),(31,10)),((30,25),(30,26)),((31,13),(31,14)),((31,15),(32,15)),((32,0),(33,0)),((32,7),(33,7)),((32,22),(32,23)),((33,4),(34,4)),((34,15),(34,16)),((34,24),(35,24)),((35,14),(36,14)),((35,18),(36,18)),((36,5),(36,6)),((36,8),(37,8)),((36,11),(36,12)),((36,11),(37,11)),((36,17),(37,17)),((37,1),(37,2)),((37,2),(37,3)),((37,5),(37,6)),((37,10),(37,11)),((38,0),(39,0)),((38,7),(38,8)),((38,8),(38,9)),((38,9),(38,10)),((38,11),(38,12)),((38,17),(38,18)),((38,26),(39,26)),((39,12),(39,13)))



equal_actual_pairs=list(same_pairs)#这两个在实际解题中是需要变的
cancal_actual_pairs=list(diff_pairs)
#等号两边一定藏着不等号
for i in equal_actual_pairs:
    if i[0][0]==i[1][0]:#同行
        if i[0][1]>0 and (((i[0][0],i[0][1]-1),i[0]) not in cancal_actual_pairs):
            cancal_actual_pairs.append(((i[0][0],i[0][1]-1),i[0]))
        if i[1][1]<width-1 and ((i[1],(i[1][0],i[1][1]+1)) not in cancal_actual_pairs):
            cancal_actual_pairs.append((i[1],(i[1][0],i[1][1]+1)))
    else:#同列
        if i[0][0]>0 and (((i[0][0]-1,i[0][1]),i[0]) not in cancal_actual_pairs):
            cancal_actual_pairs.append(((i[0][0]-1,i[0][1]),i[0]))
        if i[1][0]<height-1 and ((i[1],(i[1][0]+1,i[1][1])) not in cancal_actual_pairs):
            cancal_actual_pairs.append((i[1],(i[1][0]+1,i[1][1])))
effect=1
while effect>0:
    effect=0
    #BE1.0:三连防护
    for i in range(height):
        for j in range(width):
            if grid[i][j]==-1:
                for p in range(2):
                    for q in range(-2,1):
                        effect += chick_near(i,j,p,q)
    #BE1.0:行列已满
    for i in range(height):
        count=[0,0]
        full=1
        for j in range(width):
            if grid[i][j]>=0:
                count[grid[i][j]]+=1
            else:
                full=0
        if full==1:
            continue
        if count[0]==int(width/2):
            effect+=1
            for j in range(width):
                if grid[i][j]==-1:
                    grid[i][j]=1
        if count[1]==int(width/2):
            effect+=1
            for j in range(width):
                if grid[i][j]==-1:
                    grid[i][j]=0
    for j in range(width):
        count=[0,0]
        full=1
        for i in range(height):
            if grid[i][j]>=0:
                count[grid[i][j]]+=1
            else:
                full=0
        if full==1:
            continue
        if count[0]==int(height/2):
            effect+=1
            for i in range(height):
                if grid[i][j]==-1:
                    grid[i][j]=1
        if count[1]==int(height/2):
            effect+=1
            for i in range(height):
                if grid[i][j]==-1:
                    grid[i][j]=0
    #B+E1.0:符号专项
    for i in equal_actual_pairs:
        if grid[i[0][0]][i[0][1]] != -1 and grid[i[1][0]][i[1][1]] == -1:
            grid[i[1][0]][i[1][1]]=grid[i[0][0]][i[0][1]]
            effect+=1
        if grid[i[0][0]][i[0][1]] == -1 and grid[i[1][0]][i[1][1]] != -1:
            grid[i[0][0]][i[0][1]]=grid[i[1][0]][i[1][1]]
            effect+=1
    for i in cancal_actual_pairs:
        if grid[i[0][0]][i[0][1]] != -1 and grid[i[1][0]][i[1][1]] == -1:
            grid[i[1][0]][i[1][1]]=1-grid[i[0][0]][i[0][1]]
            effect+=1
        if grid[i[0][0]][i[0][1]] == -1 and grid[i[1][0]][i[1][1]] != -1:
            grid[i[0][0]][i[0][1]]=1-grid[i[1][0]][i[1][1]]
            effect+=1
    for i in equal_actual_pairs[:]:
        if grid[i[0][0]][i[0][1]] != -1 and grid[i[1][0]][i[1][1]] != -1:
            equal_actual_pairs.remove(i)
    for i in cancal_actual_pairs[:]:
        if grid[i[0][0]][i[0][1]] != -1 and grid[i[1][0]][i[1][1]] != -1:
            cancal_actual_pairs.remove(i)
    #BE2.0:行列黑白对
    for i in range(height):
        subject=grid[i]
        result=analysis(subject,0,i)
        if result:
            for j in result:
                if grid[i][j[0]]==-1:
                    effect+=1
                    grid[i][j[0]]=j[1]
    for i in range(width):
        subject=[grid[a][i] for a in range(height)]
        result=analysis(subject,1,i)
        if result:
            for j in result:
                if grid[j[0]][i]==-1:
                    effect+=1
                    grid[j[0]][i]=j[1]

# 算完之后带上提取到的两个关系列表：
show_binairo(grid, same_pairs, diff_pairs)