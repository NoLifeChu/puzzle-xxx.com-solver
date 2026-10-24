from playwright.sync_api import sync_playwright
import tkinter as tk
from itertools import product

def fetch_tents(url="https://www.puzzle-tents.com/"):
    """
    输入帐篷网页链接（支持每日、特殊尺寸等任意页面），
    后台静默抓取并直接返回 (size, row_task, col_task, grid, tree_coords)
    - grid: 2D 矩阵，1 为树，0 为未确定/空地
    - tree_coords: 列表套元组，如 [(r, c), ...]
    """
    print(f"正在后台启动无头浏览器抓取帐篷页面: {url} ...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        # 核心等待：等待棋盘格子与线索容器全部渲染就绪
        page.wait_for_selector(".tents-cell-back .cell")
        page.wait_for_selector("#taskLeft .cell.task, #taskLeft .task")

        # 注入自动化提取脚本
        data = page.evaluate("""() => {
            let rowContainer = document.querySelector('#taskLeft') || document.querySelector('#taskRight');
            let rowEls = Array.from(rowContainer.querySelectorAll('.cell.task, .task'));
            rowEls.sort((a, b) => a.offsetTop - b.offsetTop);
            let row_task = rowEls.map(el => parseInt(el.innerText.trim())).filter(n => !isNaN(n));

            let colContainer = document.querySelector('#taskTop') || document.querySelector('#taskBottom');
            let colEls = Array.from(colContainer.querySelectorAll('.cell.task, .task'));
            colEls.sort((a, b) => a.offsetLeft - b.offsetLeft);
            let col_task = colEls.map(el => parseInt(el.innerText.trim())).filter(n => !isNaN(n));

            let size = row_task.length;

            let gridContainer = document.querySelector('.tents-cell-back') || document.querySelector('.board-back');
            let cells = Array.from(gridContainer.querySelectorAll('.cell'));
            cells.sort((a, b) => {
                let topDiff = a.offsetTop - b.offsetTop;
                if (Math.abs(topDiff) > 5) return topDiff;
                return a.offsetLeft - b.offsetLeft;
            });

            let grid = [];
            let tree_coords = [];

            for (let r = 0; r < size; r++) {
                let row = [];
                for (let c = 0; c < size; c++) {
                    let cell = cells[r * size + c];
                    if (cell && cell.classList.contains('tree-cell')) {
                        row.push(1);
                        tree_coords.push([r, c]);
                    } else {
                        row.push(0);
                    }
                }
                grid.push(row);
            }

            return {
                size: size,
                row_task: row_task,
                col_task: col_task,
                grid: grid,
                tree_coords: tree_coords
            };
        }""")

        browser.close()

        # 确保坐标转换为纯正的 Python 元组列表 [(r, c), ...]
        tree_coords = [tuple(coord) for coord in data["tree_coords"]]

        print(f"✔ 抓取成功！识别尺寸: {data['size']}x{data['size']}，共有 {len(tree_coords)} 棵树")
        return data["size"], data["row_task"], data["col_task"], data["grid"], tree_coords

def show_tents(size, row_task, col_task, grid, cor=None):
    """
    帐篷可视化窗口
    :param size: 网格大小 (int)
    :param row_task: 行要求列表 (长度为 size)
    :param col_task: 列要求列表 (长度为 size)
    :param grid: 2D 矩阵 (0: 未确定, 1: 树, 2: 帐篷, -1: 草地/不放)
    :param cor: 配对列表 [[(r_tree, c_tree), (r_tent, c_tent)], ...]
    """
    if cor is None:
        cor = []

    root = tk.Tk()
    root.title(f"Tents & Trees Solver Visualization ({size}x{size})")

    # 自适应计算单元格尺寸
    cell_size = max(24, min(36, 700 // size))
    margin_x = 55  # 左右预留显示任务数字与字母的边距
    margin_y = 55  # 上下预留边距

    canvas_w = margin_x * 2 + cell_size * size
    canvas_h = margin_y * 2 + cell_size * size

    canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="#FFFFFF")
    canvas.pack(padx=10, pady=10)

    # 颜色配置（对齐官网经典浅草绿）
    COLOR_WHITE = "#FFFFFF"
    COLOR_GRASS = "#A8EAA8"  # 官网标志性浅绿
    COLOR_GRID  = "#333333"

    def get_cell_center(r, c):
        x = margin_x + c * cell_size + cell_size / 2
        y = margin_y + r * cell_size + cell_size / 2
        return x, y

    # 1. 绘制格子背景
    for r in range(size):
        for c in range(size):
            x1 = margin_x + c * cell_size
            y1 = margin_y + r * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size

            val = grid[r][c]
            bg = COLOR_WHITE if val == 0 else COLOR_GRASS
            canvas.create_rectangle(x1, y1, x2, y2, fill=bg, outline="#CCCCCC", width=1)

    # 2. 绘制树与帐篷的连线 (若已配对)
    for pair in cor:
        if len(pair) == 2 and pair[0] is not None and pair[1] is not None:
            t_r, t_c = pair[0]
            tent_r, tent_c = pair[1]
            x1, y1 = get_cell_center(t_r, t_c)
            x2, y2 = get_cell_center(tent_r, tent_c)
            # 黑色粗短连线
            canvas.create_line(x1, y1, x2, y2, width=2.5, fill="#111111")

    # 3. 绘制图标 (树 / 帐篷)
    for r in range(size):
        for c in range(size):
            cx, cy = get_cell_center(r, c)
            val = grid[r][c]

            # 绘制树木 (绿背景 + 树冠 + 树干)
            if val == 1:
                trunk_w = max(2, cell_size * 0.08)
                trunk_h = cell_size * 0.38
                # 棕色树干
                canvas.create_rectangle(
                    cx - trunk_w, cy - trunk_h * 0.1,
                    cx + trunk_w, cy + trunk_h,
                    fill="#795548", outline="#4E342E", width=1
                )
                # 绿色圆形树冠
                canopy_r = cell_size * 0.32
                canvas.create_oval(
                    cx - canopy_r, cy - canopy_r - trunk_h * 0.2,
                    cx + canopy_r, cy + canopy_r - trunk_h * 0.2,
                    fill="#5CB85C", outline="#2E7D32", width=1.5
                )

            # 绘制帐篷 (绿背景 + 黑色三角帐篷 + 顶部标叉)
            elif val == 2:
                tent_w = cell_size * 0.30
                tent_h = cell_size * 0.30
                top_y = cy - tent_h * 0.5
                bot_y = cy + tent_h * 0.8
                # 三角帐篷主体
                canvas.create_polygon(
                    cx, top_y,
                    cx - tent_w, bot_y,
                    cx + tent_w, bot_y,
                    fill="#111111", outline="#111111"
                )
                # 帐篷顶部的标叉 (X)
                cross_s = max(2.5, cell_size * 0.1)
                canvas.create_line(cx - cross_s, top_y - cross_s, cx + cross_s, top_y + cross_s, width=1.5, fill="#111111")
                canvas.create_line(cx + cross_s, top_y - cross_s, cx - cross_s, top_y + cross_s, width=1.5, fill="#111111")

    # 4. 绘制网格边框与外粗框
    for i in range(size + 1):
        # 横线
        y = margin_y + i * cell_size
        canvas.create_line(margin_x, y, margin_x + size * cell_size, y, fill=COLOR_GRID, width=1)
        # 竖线
        x = margin_x + i * cell_size
        canvas.create_line(x, margin_y, x, margin_y + size * cell_size, fill=COLOR_GRID, width=1)
    
    # 外部加粗外框
    canvas.create_rectangle(
        margin_x, margin_y,
        margin_x + size * cell_size, margin_y + size * cell_size,
        outline="#000000", width=3
    )

    # 5. 绘制四周的行/列线索与坐标字符
    font_task = ("Arial", max(9, int(cell_size * 0.45)), "bold")
    font_sub  = ("Arial", max(8, int(cell_size * 0.32)), "normal")

    for i in range(size):
        # 列字母 (a, b, c...) 与列任务 (col_task)
        col_letter = chr(ord('a') + i) if i < 26 else f"a{chr(ord('a') + i - 26)}"
        cx = margin_x + i * cell_size + cell_size / 2

        # 顶部：上方字母，下方数字要求
        canvas.create_text(cx, margin_y - 36, text=col_letter, font=font_sub, fill="#888888")
        canvas.create_text(cx, margin_y - 16, text=str(col_task[i]), font=font_task, fill="#000000")

        # 底部：对称展示数字要求与字母
        canvas.create_text(cx, margin_y + size * cell_size + 16, text=str(col_task[i]), font=font_task, fill="#000000")
        canvas.create_text(cx, margin_y + size * cell_size + 36, text=col_letter, font=font_sub, fill="#888888")

        # 行序号 (1, 2, 3...) 与行任务 (row_task)
        cy = margin_y + i * cell_size + cell_size / 2

        # 左侧：左边数字序号，右边要求数字
        canvas.create_text(margin_x - 36, cy, text=str(i + 1), font=font_sub, fill="#888888")
        canvas.create_text(margin_x - 16, cy, text=str(row_task[i]), font=font_task, fill="#000000")

        # 右侧：对称展示数字要求与序号
        canvas.create_text(margin_x + size * cell_size + 16, cy, text=str(row_task[i]), font=font_task, fill="#000000")
        canvas.create_text(margin_x + size * cell_size + 36, cy, text=str(i + 1), font=font_sub, fill="#888888")

    root.mainloop()

def find_neigh(y,x):
    result=[]
    if y>0 and grid[y-1][x]!=-1:#短路求值大成
        result.append((y-1,x))#只要不是绿色就行，具体看怎么筛选
    if y<size-1 and grid[y+1][x]!=-1:
        result.append((y+1,x))
    if x>0 and grid[y][x-1]!=-1:
        result.append((y,x-1))
    if x<size-1 and grid[y][x+1]!=-1:
        result.append((y,x+1))
    return result

def find_neigh_tian(left_aim,location,egnar):
    result=[]
    for i in egnar:
        if location[0]+i[0]>=0 and location[0]+i[0]<size and location[1]+i[1]>=0 and location[1]+i[1]<size:
            if (location[0]+i[0],location[1]+i[1]) in left_aim:
                result.append((location[0]+i[0],location[1]+i[1]))
    return result


def divide(aim,parts):
    left_aim=aim[:]
    result=[]
    while True:
        divide_effect=1
        while divide_effect>0:
            divide_effect=0
            for i in left_aim:#先处理最能贪心的一种
                empty=[]
                for j in ([(-1,-1),(0,-1),(1,-1)],[(1,-1),(1,0),(1,1)],[(1,1),(0,1),(-1,1)],[(-1,1),(-1,0),(-1,-1)]):
                    empty.append(find_neigh_tian(left_aim,i,j))
                if not (empty[0] or empty[1]):
                    tian=[(-1,1),(-1,0),(0,1),(0,0)]
                elif not (empty[1] or empty[2]):
                    tian=[(-1,-1),(-1,0),(0,-1),(0,0)]
                elif not (empty[2] or empty[3]):
                    tian=[(1,-1),(1,0),(0,-1),(0,0)]
                elif not (empty[3] or empty[0]):
                    tian=[(1,1),(1,0),(0,1),(0,0)]
                else:
                    continue
                part=[]
                for k in tian:
                    if i[0]+k[0]>=0 and i[0]+k[0]<size and i[1]+k[1]>=0 and i[1]+k[1]<size:
                        if (i[0]+k[0],i[1]+k[1]) in left_aim :
                            part.append((i[0]+k[0],i[1]+k[1]))
                            left_aim.remove((i[0]+k[0],i[1]+k[1]))
                            divide_effect+=1
                result.append(part)
        if not left_aim:
            if len(result)==parts:
                return result
            else:
                return []
        else:
            #处理更不贪心的情况,找出一个就收手去尝试更能贪心的
            for i in left_aim[:]:#先处理最能贪心的一种
                empty=[]
                for j in ([(-1,-1),(0,-1),(1,-1)],[(1,-1),(1,0),(1,1)],[(1,1),(0,1),(-1,1)],[(-1,1),(-1,0),(-1,-1)]):
                    empty.append(find_neigh_tian(left_aim,i,j))
                if not empty[0]:
                    tian=[(-1,1),(-1,0),(0,1),(0,0)]
                elif not empty[1]:
                    tian=[(-1,-1),(-1,0),(0,-1),(0,0)]
                elif not empty[2]:
                    tian=[(1,-1),(1,0),(0,-1),(0,0)]
                elif not empty[3]:
                    tian=[(1,1),(1,0),(0,1),(0,0)]
                else:
                    continue
                part=[]
                for k in tian:
                    if i[0]+k[0]>=0 and i[0]+k[0]<size and i[1]+k[1]>=0 and i[1]+k[1]<size:
                        if (i[0]+k[0],i[1]+k[1]) in left_aim :
                            part.append((i[0]+k[0],i[1]+k[1]))
                            left_aim.remove((i[0]+k[0],i[1]+k[1]))
                            divide_effect+=1
                result.append(part)
                break

def tian_cover(pair,tian):
    tian_location=[]
    delta=0
    for i in tian:
        if 0<=pair[0][0]+i[0]<size and 0<=pair[0][1]+i[1]<size:
            tian_location.append((pair[0][0]+i[0],pair[0][1]+i[1]))
    for i in pair:
        if i not in tian_location:
            return delta
    for i in tian_location:
        if i not in pair:
            if grid[i[0]][i[1]]==0:
                grid[i[0]][i[1]]=-1
                delta+=1
    return delta

def pairs_divide(aim,left_stars,pairs):
    involved_pairs=[]
    result=[]
    for i in pairs: 
        if set(i) & set(aim) == set(i):
            involved_pairs.append(i)
    real_pairs=[]
    involved_grids=set()
    for i in involved_pairs:
        if not set(i) & involved_grids:
            real_pairs.append(i)
            involved_grids=involved_grids | set(i)
    if len(real_pairs) == left_stars:
        for i in aim:
            if i not in involved_grids:
                result.append(i)
  
    if result:
        for j in result:
            grid[j[0]][j[1]]=-1
        return 1
    return 0

#size, row_task, col_task, grid, tree_coords = fetch_tents()
#这些日周月挑战都能解出来
size = 20
row_task = [8,1,3,6,3,5,3,4,4,4,3,5,3,6,1,6,2,5,2,6]
col_task = [2,6,3,5,4,5,2,6,3,5,3,3,6,2,6,1,6,2,6,4]
grid = [[0,0,1,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,1],[0,0,0,1,0,1,0,1,0,0,0,1,0,0,0,0,0,1,0,0],[0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,1,0,1],[0,1,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0],[0,0,1,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,1,0,1,0,0,0,0,1,0,0,0,0,1,0,1],[0,1,0,1,1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0],[0,1,0,0,0,0,0,1,0,1,0,1,0,0,0,0,1,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,1],[0,0,0,0,1,0,1,0,0,0,1,0,0,0,1,0,0,0,0,0],[0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0],[1,1,0,0,0,0,0,0,0,1,0,0,0,1,0,0,1,0,1,0],[0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0],[0,1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,1],[0,1,0,0,0,0,0,0,0,0,1,0,0,1,1,0,0,1,0,0],[0,0,1,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],[0,0,0,0,0,1,0,0,0,1,1,0,0,0,0,0,0,0,1,0],[0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0],[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0],[0,0,0,1,0,0,0,0,1,0,1,0,0,1,0,1,1,0,0,0]]
tree_coords = [(0, 2), (0, 10), (0, 14), (0, 19), (1, 3), (1, 5), (1, 7), (1, 11), (1, 17), (2, 6), (2, 10), (2, 17), (2, 19), (3, 1), (3, 4), (3, 13), (4, 2), (4, 3), (4, 8), (4, 9), (5, 5), (5, 7), (5, 12), (5, 17), (5, 19), (6, 1), (6, 3), (6, 4), (6, 9), (6, 14), (7, 1), (7, 7), (7, 9), (7, 11), (7, 16), (8, 16), (8, 18), (8, 19), (9, 4), (9, 6), (9, 10), (9, 14), (10, 6), (10, 12), (11, 0), (11, 1), (11, 9), (11, 13), (11, 16), (11, 18), (12, 3), (12, 6), (12, 17), (13, 1), (13, 7), (13, 10), (13, 19), (14, 1), (14, 10), (14, 13), (14, 14), (14, 17), (15, 2), (15, 4), (15, 12), (16, 5), (16, 9), (16, 10), (16, 18), (17, 4), (17, 18), (18, 0), (18, 14), (18, 18), (19, 3), (19, 8), (19, 10), (19, 13), (19, 15), (19, 16)]

size = 20
row_task = [6,2,6,3,4,4,1,7,1,7,2,4,4,3,7,1,6,3,4,5]
col_task = [8,1,6,3,5,4,3,3,5,2,6,2,5,3,2,5,2,6,2,7]
grid = [[0,1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0],[0,1,0,0,0,0,0,0,1,1,0,0,0,1,0,0,1,0,0,1],[0,0,1,0,0,0,0,0,0,0,1,1,0,0,0,0,1,0,1,0],[0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0],[0,1,0,0,0,0,0,1,0,0,0,0,1,0,1,0,0,0,0,0],[0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[1,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,1,0,0,1,0,0,1,0,1,0,0,1,1,0],[1,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,1,0,0],[0,0,0,0,1,1,0,0,0,0,1,0,0,0,0,0,1,0,1,0],[0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0],[0,1,0,0,1,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1],[0,0,1,0,0,0,0,0,1,0,0,1,1,0,0,0,0,0,0,0],[1,0,0,1,0,1,0,1,0,0,0,0,0,0,0,0,0,1,0,1],[0,0,0,0,0,0,1,0,1,0,0,0,0,0,1,1,0,0,0,0],[0,0,1,0,0,1,0,0,1,1,0,1,0,0,0,0,1,0,0,1],[0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[1,0,1,0,0,0,0,0,1,0,0,0,0,0,1,0,1,0,1,0],[0,1,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0]]
tree_coords = [(0, 1), (0, 3), (0, 5), (0, 16), (1, 1), (1, 8), (1, 9), (1, 13), (1, 16), (1, 19), (2, 2), (2, 10), (2, 11), (2, 16), (2, 18), (3, 4), (3, 16), (3, 18), (4, 1), (4, 7), (4, 12), (4, 14), (5, 2), (6, 0), (6, 4), (6, 10), (7, 6), (7, 9), (7, 12), (7, 14), (7, 17), (7, 18), (8, 0), (8, 3), (8, 8), (8, 17), (9, 4), (9, 5), (9, 10), (9, 16), (9, 18), (10, 9), (10, 10), (11, 1), (11, 4), (11, 7), (11, 16), (12, 11), (12, 19), (13, 2), (13, 8), (13, 11), (13, 12), (14, 0), (14, 3), (14, 5), (14, 7), (14, 17), (14, 19), (15, 6), (15, 8), (15, 14), (15, 15), (16, 2), (16, 5), (16, 8), (16, 9), (16, 11), (16, 16), (16, 19), (17, 4), (18, 0), (18, 2), (18, 8), (18, 14), (18, 16), (18, 18), (19, 1), (19, 5), (19, 11)]

size = 20
row_task = [5,4,5,3,6,3,5,3,4,3,4,4,4,1,7,2,6,3,2,6]
col_task = [5,3,2,7,2,5,4,4,4,3,5,4,2,3,5,3,4,5,3,7]
grid = [[0,0,1,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0],[0,0,0,0,1,0,1,0,0,0,0,1,0,0,0,0,1,1,0,1],[1,0,0,0,0,1,0,0,1,0,0,1,0,0,0,0,0,1,0,0],[1,0,1,0,1,0,0,1,0,0,0,0,0,0,0,1,0,1,0,0],[0,1,0,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0],[0,0,0,1,0,1,0,1,0,1,0,0,0,0,0,0,0,0,0,1],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0],[1,0,0,0,0,1,0,0,0,1,0,0,0,0,0,1,0,0,0,1],[0,1,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,1,1,0,0],[0,0,0,0,0,1,1,0,0,0,1,0,0,0,0,1,0,0,0,0],[1,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0],[0,1,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,1],[0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0],[0,0,0,0,1,0,1,1,0,1,0,0,0,0,0,0,1,0,0,0],[0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1],[1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,1,0,0],[0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1],[0,1,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0],[0,0,0,0,1,0,0,0,1,0,1,0,0,0,1,1,0,0,1,0]]
tree_coords = [(0, 2), (0, 9), (0, 14), (1, 4), (1, 6), (1, 11), (1, 16), (1, 17), (1, 19), (2, 0), (2, 5), (2, 8), (2, 11), (2, 17), (3, 0), (3, 2), (3, 4), (3, 7), (3, 15), (3, 17), (4, 1), (4, 5), (4, 14), (5, 3), (5, 5), (5, 7), (5, 9), (5, 19), (6, 17), (6, 18), (7, 0), (7, 5), (7, 9), (7, 15), (7, 19), (8, 1), (8, 2), (8, 7), (9, 8), (9, 12), (9, 16), (9, 17), (10, 5), (10, 6), (10, 10), (10, 15), (11, 0), (11, 2), (11, 7), (11, 18), (12, 1), (12, 13), (12, 14), (12, 19), (13, 13), (14, 4), (14, 6), (14, 7), (14, 9), (14, 16), (15, 5), (15, 18), (15, 19), (16, 0), (16, 4), (16, 8), (16, 12), (16, 16), (16, 17), (17, 10), (17, 19), (18, 1), (18, 5), (18, 11), (19, 4), (19, 8), (19, 10), (19, 14), (19, 15), (19, 18)]

size = 25
row_task = [7,3,8,1,9,0,9,2,7,3,5,6,5,6,4,8,2,7,3,6,3,4,4,5,8]
col_task = [11,0,9,4,5,2,7,5,3,8,3,5,4,7,4,5,3,7,4,6,2,8,3,3,7]
grid = [[0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1,0,0,0,1,0,1],[1,0,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,1,0,1,0,1,0,0,0],[0,1,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0],[1,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,1],[0,0,1,0,0,0,0,0,0,0,1,0,0,0,1,0,1,0,0,0,0,0,0,0,0],[0,0,0,1,0,0,1,0,0,1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0],[0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0,1,0,0],[1,0,0,0,0,0,0,1,0,0,0,0,1,1,1,0,0,0,1,0,0,0,0,0,0],[1,0,0,1,1,0,1,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,1],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0],[0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,1,0,1,0,0,0,0,0],[0,0,1,0,1,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0],[1,0,0,1,0,0,0,0,1,0,0,0,0,0,0,1,0,1,0,0,0,0,1,0,0],[0,1,0,0,0,0,0,0,1,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0],[1,1,0,0,0,1,0,0,0,0,1,0,1,1,0,0,1,0,0,1,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,1],[1,0,0,0,1,0,0,0,1,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0],[0,0,1,0,0,0,0,1,0,1,0,1,0,0,0,0,1,0,0,0,0,0,1,0,1],[1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0],[0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],[1,0,1,0,0,0,1,0,0,0,0,1,1,0,1,0,0,1,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0],[0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],[1,0,0,0,0,0,0,0,0,1,1,1,0,1,0,0,1,1,0,0,1,1,0,0,0]]
tree_coords = [(0, 8), (0, 13), (0, 18), (0, 22), (0, 24), (1, 0), (1, 2), (1, 7), (1, 8), (1, 17), (1, 19), (1, 21), (2, 1), (2, 4), (2, 11), (2, 20), (3, 0), (3, 6), (3, 13), (3, 20), (3, 24), (4, 2), (4, 10), (4, 14), (4, 16), (5, 3), (5, 6), (5, 9), (5, 15), (5, 18), (6, 6), (6, 10), (6, 20), (6, 22), (7, 0), (7, 7), (7, 12), (7, 13), (7, 14), (7, 18), (8, 0), (8, 3), (8, 4), (8, 6), (8, 10), (8, 14), (8, 24), (9, 17), (9, 22), (10, 5), (10, 13), (10, 17), (10, 19), (11, 2), (11, 4), (11, 7), (11, 8), (11, 21), (11, 22), (12, 0), (12, 3), (12, 8), (12, 15), (12, 17), (12, 22), (13, 1), (13, 8), (13, 11), (13, 14), (14, 0), (14, 1), (14, 5), (14, 10), (14, 12), (14, 13), (14, 16), (14, 19), (15, 13), (15, 21), (15, 24), (16, 0), (16, 4), (16, 8), (16, 14), (16, 19), (17, 2), (17, 7), (17, 9), (17, 11), (17, 16), (17, 22), (17, 24), (18, 0), (18, 1), (18, 18), (18, 22), (19, 8), (19, 24), (20, 0), (20, 2), (20, 6), (20, 11), (20, 12), (20, 14), (20, 17), (21, 7), (21, 8), (21, 20), (21, 24), (22, 14), (22, 19), (23, 2), (23, 3), (23, 4), (23, 5), (23, 24), (24, 0), (24, 9), (24, 10), (24, 11), (24, 13), (24, 16), (24, 17), (24, 20), (24, 21)]

size = 30
row_task = [8,5,8,3,8,6,6,6,7,5,3,11,2,7,5,6,6,7,4,10,4,7,4,8,3,6,5,6,4,10]
col_task = [4,9,2,8,5,6,7,4,10,3,8,6,4,8,5,9,3,7,6,5,8,4,6,5,5,7,6,6,5,9]
grid = [[0,0,1,0,1,0,0,0,0,1,0,0,0,1,0,0,1,0,0,0,0,0,0,1,0,0,0,1,0,0],[0,1,0,0,0,1,0,0,1,0,0,0,0,0,0,0,1,0,0,0,1,1,0,0,0,0,0,0,0,0],[1,0,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,1,1,0,0],[0,0,0,0,0,1,0,1,0,0,1,1,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,1],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0],[0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,1],[1,0,0,1,0,0,1,0,0,0,0,0,0,1,0,1,0,0,0,0,1,0,0,0,0,0,0,1,1,0],[1,0,0,1,0,1,0,0,0,1,0,0,0,0,1,0,0,1,0,1,0,0,0,0,0,1,0,0,0,0],[0,1,0,0,1,0,0,0,1,0,0,0,1,0,0,1,1,0,0,0,0,1,0,0,1,0,1,0,1,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0],[0,0,1,0,0,1,0,1,0,0,0,0,1,0,1,0,0,0,1,0,0,0,0,0,1,0,0,1,0,1],[0,1,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,1,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0],[0,0,0,0,0,0,0,1,0,1,0,1,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,1],[1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,1,0,0,0,0,0],[1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,1,0,0,0,0,1,0,0,0,0,1,0,0,0],[0,0,0,1,0,0,1,0,0,1,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,1,0],[0,0,0,0,1,0,0,0,0,0,0,0,1,0,1,0,0,1,0,0,0,0,0,1,0,1,0,0,0,0],[0,0,0,0,0,0,1,1,0,0,1,0,1,1,0,0,0,0,0,0,0,1,0,0,1,0,0,0,1,0],[0,0,0,1,0,0,0,0,1,0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0,0,0,1,0,0],[0,1,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1,0,1,0,0,0,1,0,1,0,0],[0,0,1,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0],[0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,1,0],[0,1,0,0,0,0,0,0,1,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0],[1,0,0,0,1,0,1,0,0,0,1,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,1,0,1,0,0,0,1,0,1,0,0],[1,0,1,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,1,0,1,0,0,0,0,0,0,0],[0,1,0,0,0,1,0,0,1,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,1,0,0,0,0,0,0,0,1,0,1,0,0,0,1,0,0,0,1,0,0,1,0,0,1,1],[0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1,1,0,0,0,0,0,1,0]]
tree_coords = [(0, 2), (0, 4), (0, 9), (0, 13), (0, 16), (0, 23), (0, 27), (1, 1), (1, 5), (1, 8), (1, 16), (1, 20), (1, 21), (2, 0), (2, 4), (2, 13), (2, 24), (2, 26), (2, 27), (3, 5), (3, 7), (3, 10), (3, 11), (3, 15), (3, 23), (3, 29), (4, 20), (4, 24), (5, 7), (5, 12), (5, 17), (5, 21), (5, 29), (6, 0), (6, 3), (6, 6), (6, 13), (6, 15), (6, 20), (6, 27), (6, 28), (7, 0), (7, 3), (7, 5), (7, 9), (7, 14), (7, 17), (7, 19), (7, 25), (8, 1), (8, 4), (8, 8), (8, 12), (8, 15), (8, 16), (8, 21), (8, 24), (8, 26), (8, 28), (9, 20), (9, 22), (10, 2), (10, 5), (10, 7), (10, 12), (10, 14), (10, 18), (10, 24), (10, 27), (10, 29), (11, 1), (11, 9), (11, 14), (12, 5), (12, 6), (12, 8), (12, 25), (12, 26), (13, 7), (13, 9), (13, 11), (13, 15), (13, 23), (13, 29), (14, 0), (14, 8), (14, 19), (14, 20), (14, 24), (15, 0), (15, 7), (15, 15), (15, 16), (15, 21), (15, 26), (16, 3), (16, 6), (16, 9), (16, 11), (16, 20), (16, 27), (16, 28), (17, 4), (17, 12), (17, 14), (17, 17), (17, 23), (17, 25), (18, 6), (18, 7), (18, 10), (18, 12), (18, 13), (18, 21), (18, 24), (18, 28), (19, 3), (19, 8), (19, 13), (19, 15), (19, 18), (19, 20), (19, 27), (20, 1), (20, 4), (20, 10), (20, 19), (20, 21), (20, 25), (20, 27), (21, 2), (21, 13), (21, 14), (21, 22), (21, 28), (22, 7), (22, 20), (22, 22), (22, 28), (23, 1), (23, 8), (23, 10), (23, 16), (23, 24), (24, 0), (24, 4), (24, 6), (24, 10), (24, 14), (24, 16), (25, 8), (25, 13), (25, 19), (25, 21), (25, 25), (25, 27), (26, 0), (26, 2), (26, 9), (26, 15), (26, 20), (26, 22), (27, 1), (27, 5), (27, 8), (27, 9), (27, 18), (28, 4), (28, 12), (28, 14), (28, 18), (28, 22), (28, 25), (28, 28), (28, 29), (29, 11), (29, 17), (29, 21), (29, 22), (29, 28)]

size = 15
row_task = [4,3,2,3,3,3,4,2,3,4,1,4,3,2,4]
col_task = [6,1,3,2,4,2,3,2,3,2,4,2,3,4,4]
grid = [[0,0,1,0,0,0,0,0,0,0,0,0,0,0,1],[1,0,0,0,1,0,1,0,0,1,0,0,1,0,0],[0,0,0,0,0,0,0,0,1,0,0,0,0,0,0],[0,1,0,0,0,1,0,0,0,0,0,0,0,0,1],[0,0,0,0,0,0,0,1,0,0,0,1,1,0,0],[0,0,1,0,0,0,0,1,0,1,0,0,0,1,0],[1,1,0,0,0,1,0,1,0,0,1,0,0,0,0],[0,1,0,1,0,0,0,0,0,0,0,0,0,0,1],[1,0,0,0,0,1,0,0,1,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,1,0,0,1,0,0],[0,0,0,0,0,0,0,0,0,0,1,0,0,1,0],[0,0,1,0,0,0,1,1,0,0,0,0,0,1,1],[0,1,0,0,1,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,1,0,0,0,0,0,1,1,0],[1,0,0,0,0,0,0,0,1,0,0,0,0,0,0]]
tree_coords = [(0, 2), (0, 14), (1, 0), (1, 4), (1, 6), (1, 9), (1, 12), (2, 8), (3, 1), (3, 5), (3, 14), (4, 7), (4, 11), (4, 12), (5, 2), (5, 7), (5, 9), (5, 13), (6, 0), (6, 1), (6, 5), (6, 7), (6, 10), (7, 1), (7, 3), (7, 14), (8, 0), (8, 5), (8, 8), (9, 9), (9, 12), (10, 10), (10, 13), (11, 2), (11, 6), (11, 7), (11, 13), (11, 14), (12, 1), (12, 4), (13, 6), (13, 12), (13, 13), (14, 0), (14, 8)]

#grid含义：0为未确定（白），1为树，2为帐篷，-1为叉（绿）
def main(size, row_task, col_task, grid, tree_coords:list):
    #初始化
    #额外定义main是因为这里可以自由修改各种参数，而不改变原始数据；除了size都会被消去，但只有grid被接收，所以无所谓
    row_task=row_task[:]
    col_task=col_task[:]
    tree_coords=tree_coords[:]


    cor=[]#配对关系，树：帐篷

    #复用星之战
    divided=set()#(类别,编号)
    pairs=[]

    tree_access={}
    for tree in tree_coords:
        tree_access[tree]=find_neigh(*tree)

    #和树不沾边的全部叉掉；因为树在不断减少，这每轮都要做一次
    safe=set()
    for tree in tree_access:
        safe.update(tree_access[tree])

    for i, j in product(range(size), range(size)):
        if ((i,j) not in safe) and grid[i][j]==0:
            grid[i][j]=-1

    #主循环；这里比起last_xxx还是用effect方便，因为grid和cor变一个就说明有进展
    effect=1
    while effect>0:
        effect=0
        #树在减少，树可达也一起减少
        for tree in list(tree_access.keys()):
            if tree not in tree_coords:
                del tree_access[tree]

        #和树不沾边的全部叉掉；因为树在不断减少，这每轮都要做一次
        safe=set()
        for tree in tree_access:
            safe.update(tree_access[tree])

        for i, j in product(range(size), range(size)):
            if ((i,j) not in safe) and grid[i][j]==0:
                grid[i][j]=-1
        #最简单：如果一个树周围只有一个可达，那还说什么
        for tree in tree_coords:
            air=[i for i in tree_access[tree] if grid[i[0]][i[1]]==0]
            tents=[i for i in tree_access[tree] if grid[i[0]][i[1]]==2]
            if len(air)==1 and (not tents):
                i=air
                
                for y,x in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)):
                    if 0<=i[0][0]+y<size and 0<=i[0][1]+x<size and grid[i[0][0]+y][i[0][1]+x]==0:
                        grid[i[0][0]+y][i[0][1]+x]=-1
                grid[i[0][0]][i[0][1]]=2
                effect+=1
        
        #复用星之战代码
        for y in range(size):#单行考虑
            if (0,y) not in divided:#还活着
                aim=[]#包含这个宫格所有活着的坐标元组
                left_tents=row_task[y]
                for x in range(size):
                    if grid[y][x]==0:
                        aim.append((y,x))
                    if grid[y][x]==2:
                        left_tents-=1
                divide_result=divide(aim,left_tents)
                if divide_result:#成功分割
                    divided.add((0,y))
                    for j in divide_result:
                        pairs.append(j)
                else:#融入数对
                    if pairs_divide(aim,left_tents,pairs)>0:
                        effect+=pairs_divide(aim,left_tents,pairs)
                    else:#弱化版一步假设
                        divide_result=divide(aim,left_tents+1)
                        if divide_result:#只多一个
                            for y1 in (y-1,y+1):
                                if 0<=y1<size:
                                    for x in range(size):
                                        if grid[y1][x]==0:
                                            aim1=aim[:]
                                            for i in aim1[:]:
                                                if -1<=i[0]-y1<=1 and -1<=i[1]-x<=1:
                                                    aim1.remove(i)
                                            divide_result=divide(aim1,left_tents-1)
                                            if divide_result:#减没了！
                                                grid[y1][x]=-1
                                                effect+=1
        
        for x in range(size):#单列考虑
            if (1,x) not in divided:#还活着
                aim=[]#包含这个宫格所有活着的坐标元组
                left_tents=col_task[x]
                for y in range(size):
                    if grid[y][x]==0:
                        aim.append((y,x))
                    if grid[y][x]==2:
                        left_tents-=1
                divide_result=divide(aim,left_tents)
                if divide_result:#成功分割
                    divided.add((1,x))
                    for j in divide_result:
                        pairs.append(j)
                else:#融入数对
                    if pairs_divide(aim,left_tents,pairs)>0:
                        effect+=pairs_divide(aim,left_tents,pairs)
                    else:#弱化版一步假设
                        divide_result=divide(aim,left_tents+1)
                        if divide_result:#只多一个
                            for x1 in (x-1,x+1):
                                if 0<=x1<size:
                                    for y in range(size):
                                        if grid[y][x1]==0:
                                            aim1=aim[:]
                                            for i in aim1[:]:
                                                if -1<=i[0]-y<=1 and -1<=i[1]-x1<=1:
                                                    aim1.remove(i)
                                            divide_result=divide(aim1,left_tents-1)
                                            if divide_result:#减没了！
                                                grid[y][x1]=-1
                                                effect+=1

        for y in range(size-1):#双行考虑
            if (2,y) not in divided:#还活着
                aim=[]#包含这个宫格所有活着的坐标元组
                left_tents=row_task[y]+row_task[y+1]
                for x in range(size):
                    if grid[y][x]==0:
                        aim.append((y,x))
                    if grid[y][x]==2:
                        left_tents-=1
                    if grid[y+1][x]==0:
                        aim.append((y+1,x))
                    if grid[y+1][x]==2:
                        left_tents-=1
                divide_result=divide(aim,left_tents)
                if divide_result:#成功分割
                    divided.add((2,y))
                    for j in divide_result:
                        pairs.append(j)
                
        
        for x in range(size-1):#双列考虑
            if (3,x) not in divided:#还活着
                aim=[]#包含这个宫格所有活着的坐标元组
                left_tents=col_task[x]+col_task[x+1]
                for y in range(size):
                    if grid[y][x]==0:
                        aim.append((y,x))
                    if grid[y][x]==2:
                        left_tents-=1
                    if grid[y][x+1]==0:
                        aim.append((y,x+1))
                    if grid[y][x+1]==2:
                        left_tents-=1
                divide_result=divide(aim,left_tents)
                if divide_result:#成功分割
                    divided.add((3,x))
                    for j in divide_result:
                        pairs.append(j)

        if not all(pairs):#出错，有配对的格子全空了，说明有帐篷放错了地方
            print(pairs)
        
        for i in pairs[:]:#最后处理方格对
            if len(i)==1:#直接放
                #print(i)
                for y,x in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)):
                    if 0<=i[0][0]+y<size and 0<=i[0][1]+x<size and grid[i[0][0]+y][i[0][1]+x]==0:
                        grid[i[0][0]+y][i[0][1]+x]=-1
                grid[i[0][0]][i[0][1]]=2
                effect+=1
                pairs.remove(i)
            else:
                if len(i)>0:
                    if len(i)<4:
                        
                        effect+=tian_cover(i,[(-1,1),(-1,0),(0,1),(0,0)])
                        effect+=tian_cover(i,[(-1,-1),(-1,0),(0,-1),(0,0)])
                        effect+=tian_cover(i,[(1,-1),(1,0),(0,-1),(0,0)])
                        effect+=tian_cover(i,[(1,1),(1,0),(0,1),(0,0)])
                    i_del=0
                    for j in i[:]:
                        if grid[j[0]][j[1]]==-1:
                            i.remove(j)
                            effect+=1
                        if grid[j[0]][j[1]]==2:
                            i_del=1
                    if i_del==1:
                        pairs.remove(i)

        if not all(pairs):#出错
            print(pairs)

        

        
        for tree in tree_coords[:]:#树去配对帐篷
            air=[i for i in tree_access[tree] if grid[i[0]][i[1]]==0]
            tents=[i for i in tree_access[tree] if grid[i[0]][i[1]]==2]
            if (not air) and len(tents)==1:#配对成功
                tent=tents[0]
                #print(tree,tents[0])
                cor.append((tree,tent))#加入结果
                if 1:
                    row_task[tent[0]]-=1
                    col_task[tent[1]]-=1
                    grid[tent[0]][tent[1]]=-1
                    grid[tree[0]][tree[1]]=-1
                    tree_coords.remove(tree)#直接被遗忘
                    #检查防止误报空列表
                    for i in pairs[:]:#帐篷已经有了，配对可以删了
                        if tent in i:
                            pairs.remove(i)
                effect+=1

        for y, x in product(range(size), range(size)):#帐篷去配对树
            if grid[y][x]==2:
                tent_access=find_neigh(y,x)
                tree_to_tent=[]
                for i in tent_access:
                    if grid[i[0]][i[1]]==1:
                        tree_to_tent.append(i)
                if len(tree_to_tent)==1:#配对成功
                    tree=tree_to_tent[0]
                    tent=(y,x)
                    cor.append((tree,tent))#加入结果
                    if 1:
                        row_task[tent[0]]-=1
                        col_task[tent[1]]-=1
                        grid[tent[0]][tent[1]]=-1
                        grid[tree[0]][tree[1]]=-1
                        tree_coords.remove(tree)#直接被遗忘
                        #检查防止误报空列表
                        for i in pairs[:]:#帐篷已经有了，配对可以删了
                            if tent in i:
                                pairs.remove(i)
                    effect+=1

        print(effect)
    return grid,cor



if sum(row_task)!=sum(col_task) or sum(row_task)!=len(tree_coords):
    print('不！')
else:
    print(f'共{len(tree_coords)}树')

grid,cor=main(size, row_task, col_task, grid, tree_coords)
#grid已经被消去过了，现在把它还原回去
for i in cor:
    if None not in i:
        grid[i[0][0]][i[0][1]]=1
        grid[i[1][0]][i[1][1]]=2



show_tents(size, row_task, col_task, grid, cor)