from playwright.sync_api import sync_playwright
import tkinter as tk

def fetch_binairo(url="https://www.puzzle-binairo.com/"):
    """
    输入黑白（Binairo）页面链接（支持每日 24x24、每月 30x40 等任意尺寸），
    后台静默抓取并直接返回 (width, height, grid)
    其中 grid 为 height * width 的二维列表，取值为 1(黑), 0(白), -1(未知)
    """
    print(f"正在后台启动无头浏览器抓取黑白题目: {url} ...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        # 等待棋盘元素渲染完成
        page.wait_for_selector('div[tabindex="-1"]')

        # 注入提取脚本
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
                    if (Math.abs(k - top) < 5) {
                        foundKey = k;
                        break;
                    }
                }
                if (foundKey === null) {
                    foundKey = top;
                    rowsMap.set(foundKey, []);
                }
                rowsMap.get(foundKey).push(c);
            });

            let sortedRowTops = Array.from(rowsMap.keys()).sort((a, b) => a - b);
            let height = sortedRowTops.length;
            let width = rowsMap.get(sortedRowTops[0]).length;

            let grid = [];
            for (let topKey of sortedRowTops) {
                let rowCells = rowsMap.get(topKey);
                rowCells.sort((a, b) => a.offsetLeft - b.offsetLeft);

                let rowData = [];
                for (let c of rowCells) {
                    if (c.classList.contains('cell-1')) {
                        rowData.push(1);
                    } else if (c.classList.contains('cell-0')) {
                        rowData.push(0);
                    } else {
                        rowData.push(-1);
                    }
                }
                grid.push(rowData);
            }

            return { width: width, height: height, grid: grid };
        }""")

        browser.close()
        print(f"✔ 抓取成功！尺寸: 宽 {data['width']} x 高 {data['height']}")
        return data["width"], data["height"], data["grid"]

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

def analysis(subject):#这次用数对的思想处理
    #0.计算缺口
    gap=[int(len(subject)/2)]*2
    for i in subject:
        if i != -1:
            gap[i]-=1
    #1.提取空当
    space=[a for a in range(len(subject)) if subject[a]==-1]
    #2.不用去除数对
    pairs=[]

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








# 自动抓取模式
#width, height, grid = fetch_binairo("https://cn.puzzle-binairo.com/monthly-binairo/")

# 手动降级模式（如果用提取器.js直接贴）
width = 30
height = 40
grid = [[-1,1,0,1,0,0,1,0,-1,1,0,1,0,1,-1,0,1,0,0,1,1,0,1,-1,-1,0,1,0,-1,1],[1,0,0,1,0,1,-1,-1,-1,1,0,1,1,0,0,1,0,1,1,0,0,1,-1,0,1,0,0,1,0,1],[0,1,1,0,1,0,0,1,1,0,1,0,1,0,1,1,0,0,1,0,1,0,-1,-1,0,1,0,1,1,0],[1,0,0,1,0,1,1,0,0,1,0,1,0,1,1,0,1,0,0,1,1,0,0,1,1,0,1,0,0,1],[0,1,0,1,1,0,1,1,0,1,1,0,0,1,0,1,0,1,1,0,0,1,-1,-1,0,1,0,0,1,0],[1,0,1,0,1,0,0,1,1,0,-1,-1,1,0,1,0,-1,-1,0,1,0,0,1,0,1,-1,-1,1,-1,-1],[0,1,0,1,0,1,-1,0,1,0,0,1,0,-1,-1,1,-1,0,1,0,1,1,0,1,0,-1,-1,0,-1,1],[0,0,1,0,1,0,1,1,0,1,1,0,1,-1,-1,0,-1,-1,0,1,0,0,1,1,0,1,0,1,1,0],[1,0,1,0,-1,-1,-1,0,1,0,0,1,0,0,1,-1,0,1,1,0,1,1,0,0,1,0,1,-1,0,1],[1,1,0,1,0,1,0,1,-1,0,1,0,0,1,-1,-1,-1,0,1,0,1,0,1,0,-1,-1,0,-1,-1,0],[0,-1,1,0,-1,-1,-1,-1,-1,1,0,1,1,0,0,1,1,0,0,1,0,1,0,1,-1,-1,1,-1,-1,1],[0,0,1,0,1,-1,-1,0,1,1,0,1,1,0,1,0,0,1,0,1,1,0,1,1,0,0,1,0,1,0],[1,1,0,1,0,0,1,1,0,0,1,0,0,1,0,1,1,0,1,0,0,1,1,0,1,1,0,1,0,0],[0,0,1,1,0,1,0,0,1,0,0,1,0,0,1,1,0,1,0,1,1,0,0,1,0,1,1,0,1,1],[1,1,0,0,1,0,0,1,0,1,1,0,1,0,1,0,1,1,0,0,1,1,0,1,0,0,1,0,0,1],[1,0,1,1,0,1,1,0,0,1,0,0,1,1,0,1,0,0,1,1,0,0,1,0,1,0,0,1,1,0],[0,0,1,0,1,1,0,1,1,0,1,1,0,1,1,0,0,1,0,1,0,1,-1,-1,-1,1,0,1,0,0],[0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,1,0,1,0,1,1,0,1,0,0,1,0,1,1],[1,1,0,1,0,-1,-1,1,0,1,0,1,0,0,1,0,1,1,0,0,1,0,1,0,1,1,0,0,1,0],[-1,0,1,0,1,-1,-1,0,1,1,0,0,1,1,0,1,0,0,1,1,0,0,1,1,0,0,1,1,0,-1],[-1,0,1,1,0,0,1,1,0,0,1,-1,0,1,0,1,0,1,0,1,0,1,0,1,0,-1,1,-1,0,-1],[-1,1,0,0,1,1,0,0,1,0,1,1,0,0,1,0,1,0,1,0,1,1,0,0,1,1,0,-1,1,-1],[0,1,0,1,1,0,1,1,0,1,0,0,1,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,1,0],[1,0,1,0,0,1,-1,0,1,1,0,-1,1,0,-1,1,0,1,0,1,0,1,0,1,0,0,1,0,0,1],[0,1,1,0,0,1,0,1,0,0,1,1,0,1,1,0,0,1,1,0,0,1,1,0,0,1,0,1,0,1],[1,0,0,1,1,0,-1,-1,1,0,-1,-1,0,1,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0],[0,-1,1,0,0,1,-1,0,1,1,0,-1,1,0,1,0,1,0,0,1,0,0,1,1,0,-1,1,0,0,1],[1,-1,0,1,1,0,-1,1,0,1,-1,0,1,1,0,1,0,1,1,0,0,1,-1,0,-1,-1,0,1,1,0],[0,-1,1,0,1,0,1,1,0,0,1,-1,0,1,-1,0,1,0,1,0,1,1,0,-1,-1,0,1,1,0,-1],[0,1,1,0,0,1,0,0,1,0,0,1,1,0,1,0,1,1,0,1,0,0,1,1,0,1,1,0,0,1],[1,0,0,1,1,0,1,1,0,1,1,0,1,1,0,1,0,0,1,0,0,1,0,0,1,0,0,1,1,0],[1,0,1,0,0,1,1,0,0,1,0,1,0,0,1,-1,-1,1,0,0,1,1,0,1,1,0,1,0,1,0],[0,1,0,1,1,0,0,1,1,0,-1,-1,0,1,1,0,-1,-1,-1,1,0,0,1,0,0,1,1,0,0,1],[1,0,0,1,0,-1,-1,0,1,0,1,0,1,-1,0,-1,-1,-1,-1,-1,1,0,0,1,1,0,0,1,1,0],[0,1,1,0,1,-1,-1,1,0,1,0,1,1,0,0,1,1,0,1,0,0,1,-1,-1,-1,-1,0,1,0,-1],[1,-1,0,1,1,0,1,1,0,0,1,1,0,0,1,0,0,1,0,1,1,0,-1,-1,-1,-1,1,0,-1,-1],[0,0,1,0,0,1,0,0,1,1,0,0,1,1,0,1,1,0,1,1,0,-1,-1,1,0,1,0,0,1,1],[-1,-1,-1,1,0,1,1,0,1,0,-1,1,0,1,1,0,0,1,1,0,0,1,-1,-1,-1,-1,0,1,-1,0],[-1,-1,-1,0,1,0,-1,1,0,0,1,1,0,0,1,0,1,1,0,-1,1,-1,0,-1,-1,0,1,-1,-1,0],[1,1,0,1,0,-1,-1,-1,-1,1,0,0,1,0,0,1,1,0,0,1,1,0,-1,1,-1,-1,1,-1,-1,1]]

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

    #BE1.0:行列重复
    #懒得写

    #BE2.0:行列定式计数
    for i in range(height):
        subject=grid[i]
        result=analysis(subject)
        if result:
            for j in result:
                if grid[i][j[0]]==-1:
                    effect+=1
                    grid[i][j[0]]=j[1]
    for i in range(width):
        subject=[grid[a][i] for a in range(height)]
        result=analysis(subject)
        if result:
            for j in result:
                if grid[j[0]][i]==-1:
                    effect+=1
                    grid[j[0]][i]=j[1]

    #BE3.0:???


for i in range(height):
    for j in range(height):
        if i!=j:
            sim=1
            for k in range(width):
                if grid[i][k]!=grid[j][k] and grid[i][k]!=-1 and grid[j][k]!=-1:
                    sim=0
            if sim==1:
                print(i,j,'行极像！')

for i in range(width):
    for j in range(width):
        if i!=j:
            sim=1
            for k in range(height):
                if grid[k][i]!=grid[k][j] and grid[k][i]!=-1 and grid[k][j]!=-1:
                    sim=0
            if sim==1:
                print(i,j,'列极像！')

show_binairo(grid)