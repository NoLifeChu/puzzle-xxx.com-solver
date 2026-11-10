from playwright.sync_api import sync_playwright
from itertools import product
import tkinter as tk
import colorsys


class SamexButDiffbError(Exception):
    pass

class CloseError(Exception):
    pass

class UnknownError(Exception):
    pass

class Grid(list):
    """升级版二维网格：支持 grid[a] 直接访问坐标，其中a为元组"""
    def __getitem__(self, key):
        if isinstance(key, tuple):
            return super().__getitem__(key[0])[key[1]]
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            super().__getitem__(key[0])[key[1]] = value
        else:
            super().__setitem__(key, value)

def fetch_masyu(url="https://www.puzzle-masyu.com/"):
    """
    输入珍珠网页链接（支持每日、特殊尺寸等任意页面），
    物理坐标精确定位，直接返回 (size, white_pearls, black_pearls)
    - size: 正方形尺寸 (int)
    - white_pearls: 白珠真实元组列表 [(r, c), ...]
    - black_pearls: 黑珠真实元组列表 [(r, c), ...]
    """
    print(f"正在后台启动无头浏览器抓取珍珠页面: {url} ...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        # 核心等待：等棋盘所有顶点渲染就绪
        page.wait_for_selector(".loop-dot")

        data = page.evaluate("""() => {
            let board = document.querySelector('.board-back') || document.querySelector('#game') || document;
            let allDots = Array.from(board.querySelectorAll('.loop-dot'));

            function cluster(coords) {
                coords.sort((a, b) => a - b);
                let res = [];
                for (let v of coords) {
                    if (!res.length || Math.abs(v - res[res.length - 1]) > 5) {
                        res.push(v);
                    }
                }
                return res;
            }

            let rowTops = cluster(allDots.map(el => el.offsetTop));
            let colLefts = cluster(allDots.map(el => el.offsetLeft));
            let size = rowTops.length;

            function getCellCoord(el) {
                let t = el.offsetTop;
                let l = el.offsetLeft;
                let r = rowTops.findIndex(y => Math.abs(y - t) <= 5);
                let c = colLefts.findIndex(x => Math.abs(x - l) <= 5);
                return [r, c];
            }

            let whiteEls = Array.from(board.querySelectorAll('.loop-dot.dot-white'));
            let blackEls = Array.from(board.querySelectorAll('.loop-dot.dot-black'));

            let white_pearls = whiteEls.map(getCellCoord).filter(p => p[0] !== -1 && p[1] !== -1);
            let black_pearls = blackEls.map(getCellCoord).filter(p => p[0] !== -1 && p[1] !== -1);

            white_pearls.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
            black_pearls.sort((a, b) => a[0] - b[0] || a[1] - b[1]);

            return {
                size: size,
                white_pearls: white_pearls,
                black_pearls: black_pearls
            };
        }""")

        browser.close()

        white_pearls = [tuple(p) for p in data["white_pearls"]]
        black_pearls = [tuple(p) for p in data["black_pearls"]]

        print(f"✔ 抓取成功！尺寸: {data['size']}x{data['size']} (白珠: {len(white_pearls)}, 黑珠: {len(black_pearls)})")
        return data["size"], white_pearls, black_pearls


def show_masyu(size, white_pearls, black_pearls, grid):
    """
    珍珠 (Masyu) 终极拓扑对偶染色看板
    - 自动识别 grid 是否带有外围海洋，珍珠永不错位！
    - 支持鼠标任意键拖拽平移、滚轮漫游防爆屏
    - 珍珠居中渲染在 4 个对偶格子的十字晶格点上
    """
    root = tk.Tk()
    root.title("Masyu (Pearl) Dual-Coloring Solver - [按住鼠标任意键可自由拖动画布]")

    # 1. 核心自适应：自动检测 grid 是否还带着外层 0 号海洋层
    grid_h = len(grid)
    grid_w = len(grid[0])
    all_pearls = white_pearls + black_pearls
    max_p_coord = max([max(r, c) for r, c in all_pearls] or [0])

    # 如果 grid 大小大于珍珠最大坐标 + 1，说明外围海洋还在！
    has_ocean = (grid_h > max_p_coord + 1)
    offset = 1 if has_ocean else 0

    # 2. 屏幕防爆自适应尺寸
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()

    cell_size = max(26, min(48, 800 // max(grid_w, grid_h)))
    margin_x = 50
    margin_y = 50

    total_w = margin_x * 2 + cell_size * grid_w
    total_h = margin_y * 2 + cell_size * grid_h

    view_w = min(total_w + 30, int(screen_w * 0.82))
    view_h = min(total_h + 30, int(screen_h * 0.82))
    root.geometry(f"{view_w}x{view_h}+{(screen_w - view_w)//2}+{(screen_h - view_h)//2}")

    # 3. 带漫游能力的画布系统
    frame = tk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(frame, bg="#2B2B2B", scrollregion=(0, 0, total_w, total_h))
    h_bar = tk.Scrollbar(frame, orient=tk.HORIZONTAL, command=canvas.xview)
    v_bar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
    canvas.configure(xscrollcommand=h_bar.set, yscrollcommand=v_bar.set)

    h_bar.pack(side=tk.BOTTOM, fill=tk.X)
    v_bar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # 鼠标拖拽漫游
    for btn in ("<ButtonPress-1>", "<ButtonPress-2>", "<ButtonPress-3>"):
        canvas.bind(btn, lambda e: canvas.scan_mark(e.x, e.y))
    for motion in ("<B1-Motion>", "<B2-Motion>", "<B3-Motion>"):
        canvas.bind(motion, lambda e: canvas.scan_dragto(e.x, e.y, gain=1))
    canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
    canvas.bind("<Shift-MouseWheel>", lambda e: canvas.xview_scroll(int(-1 * (e.delta / 120)), "units"))

    # 4. 配色生成函数 (继承数回 x.0 / x.5 经典方案)
    def get_color_scheme(comp_id):
        if comp_id == 0:
            return "#C8C8FC", "#E57373", "#FFF2F2"  # 0.5淡紫(内), 0.0粉红网纹(外)
        h = (comp_id * 0.618033988749895) % 1.0
        r1, g1, b1 = colorsys.hsv_to_rgb(h, 0.38, 0.98)
        r2, g2, b2 = colorsys.hsv_to_rgb(h, 0.70, 0.75)
        r3, g3, b3 = colorsys.hsv_to_rgb(h, 0.12, 0.99)
        return (f"#{int(r1*255):02x}{int(g1*255):02x}{int(b1*255):02x}",
                f"#{int(r2*255):02x}{int(g2*255):02x}{int(b2*255):02x}",
                f"#{int(r3*255):02x}{int(g3*255):02x}{int(b3*255):02x}")

    def draw_mesh(x1, y1, x2, y2, bg_col, line_col):
        canvas.create_rectangle(x1, y1, x2, y2, fill=bg_col, outline="#D0D0D0", width=1)
        S, step = cell_size, max(7, cell_size // 4)
        for D in range(step, 2 * S, step):
            if D <= S: canvas.create_line(x1, y1 + D, x1 + D, y1, fill=line_col, width=1)
            else: canvas.create_line(x1 + D - S, y2, x2, y1 + D - S, fill=line_col, width=1)
        for D in range(-S + step, S, step):
            if D >= 0: canvas.create_line(x1 + D, y1, x2, y2 - D, fill=line_col, width=1)
            else: canvas.create_line(x1, y1 - D, x2 + D, y2, fill=line_col, width=1)

    # 5. 绘制所有对偶格子 (面)
    for r in range(grid_h):
        for c in range(grid_w):
            x1 = margin_x + c * cell_size
            y1 = margin_y + r * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size

            state = grid[r][c]
            if state is None or state < -0.1:
                canvas.create_rectangle(x1, y1, x2, y2, fill="#FFFFFF", outline="#D0D0D0", width=1)
            else:
                comp_id = int(state)
                polarity = 1 if (state % 1 >= 0.25) else 0
                solid_col, hatch_line, hatch_bg = get_color_scheme(comp_id)
                if polarity == 1:
                    canvas.create_rectangle(x1, y1, x2, y2, fill=solid_col, outline="#D0D0D0", width=1)
                else:
                    draw_mesh(x1, y1, x2, y2, hatch_bg, hatch_line)

    # 6. 绘制所有晶格点与珍珠 (精准咬合在十字路口上！)
    dot_r = max(2, cell_size // 14)
    pearl_r = cell_size * 0.32

    # 先绘制所有晶格黑点
    for r in range(grid_h + 1):
        for c in range(grid_w + 1):
            px = margin_x + c * cell_size
            py = margin_y + r * cell_size
            canvas.create_oval(px - dot_r, py - dot_r, px + dot_r, py + dot_r, fill="#555555", outline="")

    # 绘制白珍珠 (White Pearls)
    for pr, pc in white_pearls:
        # 核心防错位偏移：根据是否有外围海洋，自动加 offset！
        cx = margin_x + (pc + offset) * cell_size
        cy = margin_y + (pr + offset) * cell_size
        # 纯白圆底 + 粗黑描边
        canvas.create_oval(cx - pearl_r, cy - pearl_r, cx + pearl_r, cy + pearl_r,
                           fill="#FFFFFF", outline="#000000", width=2.5)

    # 绘制黑珍珠 (Black Pearls)
    for pr, pc in black_pearls:
        cx = margin_x + (pc + offset) * cell_size
        cy = margin_y + (pr + offset) * cell_size
        # 纯黑圆底 + 立体高光小圆点
        canvas.create_oval(cx - pearl_r, cy - pearl_r, cx + pearl_r, cy + pearl_r,
                           fill="#111111", outline="#000000", width=2.5)
        # 高光点
        hl_r = max(1.5, pearl_r * 0.22)
        canvas.create_oval(cx - pearl_r*0.35 - hl_r, cy - pearl_r*0.35 - hl_r,
                           cx - pearl_r*0.35 + hl_r, cy - pearl_r*0.35 + hl_r,
                           fill="#888888", outline="")

    root.mainloop()


def find_neig4(i,j):#保留旧类型，虽然可以被兼容，但这个更快啊
    return [(i+1,j),(i-1,j),(i,j+1),(i,j-1)]

def find_neig8(i,j):#注意是斜角，不是8相邻
    return [(i+1,j+1),(i+1,j-1),(i-1,j+1),(i-1,j-1)]

def find_diy(i,j,kind):#find的集大成者
    match kind:
        case 'tian':#指白珍珠需要的田
            return [(i,j),(i,j+1),(i+1,j),(i+1,j+1)]
        case 'v':#指白珍珠往竖直方向延申，共8格；致命结构是0=1≠2=3≠4……
            return [(i-1,j),(i-1,j+1),(i,j),(i,j+1),(i+1,j),(i+1,j+1),(i+2,j),(i+2,j+1)]
        case 'h':#指白珍珠往水平方向延申，共8格
            return [(i,j-1),(i+1,j-1),(i,j),(i+1,j),(i,j+1),(i+1,j+1),(i,j+2),(i+1,j+2)]
        case 'up':#以下四个是黑珍珠考虑的四格上下左右；对符合的来说，前两个相同、后两个相同；而中间两个离自己更近
            return [(i-1,j),(i,j),(i,j+1),(i-1,j+1)]
        case 'down':
            return [(i+2,j),(i+1,j),(i+1,j+1),(i+2,j+1)]
        case 'left':
            return [(i,j-1),(i,j),(i+1,j),(i+1,j-1)]
        case 'right':
            return [(i,j+2),(i,j+1),(i+1,j+1),(i+1,j+2)]
        case 4:#理论上兼容find_neig4
            return [(i+1,j),(i-1,j),(i,j+1),(i,j-1)]
        case 8:#理论上兼容find_neig8
            return [(i+1,j+1),(i+1,j-1),(i-1,j+1),(i-1,j-1)]
        case _:#其它自定义位移，此时kind是类似于[(2,2),(-1,2),……]
            result=[]
            for p in kind:
                result.append((i+p[0],j+p[1]))
            return result
        
def xor5(a,b):#5版本的异或，支持不同形式比较
    if str(float(a))==str(float(b)):
        return 0
    else:
        return 0.5

def xorint(a):#在x.0和x.5之间转换
    x = int(a)
    return x + 0.5 if a == x else float(x)



#一个简单的日挑战
size = 30
white_pearls = [(0, 6), (0, 15), (0, 16), (0, 25), (0, 28), (1, 0), (1, 13), (1, 22), (1, 23), (1, 29), (2, 23), (2, 28), (3, 12), (3, 13), (3, 14), (3, 20), (3, 21), (3, 24), (3, 25), (3, 29), (4, 0), (4, 13), (4, 17), (4, 21), (4, 27), (5, 28), (6, 4), (6, 5), (6, 15), (6, 26), (7, 1), (7, 5), (7, 20), (7, 22), (7, 26), (8, 0), (8, 11), (8, 17), (8, 22), (8, 23), (8, 29), (9, 2), (9, 4), (9, 10), (9, 22), (10, 1), (10, 7), (10, 8), (10, 10), (10, 20), (10, 26), (10, 27), (10, 28), (10, 29), (12, 0), (12, 9), (12, 21), (12, 22), (12, 23), (13, 13), (13, 18), (13, 19), (13, 27), (14, 1), (14, 20), (14, 23), (14, 29), (15, 3), (15, 10), (15, 19), (16, 8), (16, 21), (17, 1), (17, 4), (17, 15), (17, 16), (17, 21), (17, 26), (17, 29), (18, 4), (18, 5), (18, 28), (19, 5), (19, 6), (19, 9), (19, 11), (19, 22), (20, 2), (20, 3), (20, 14), (20, 25), (21, 6), (21, 8), (21, 9), (21, 19), (21, 23), (21, 26), (22, 4), (22, 14), (22, 24), (23, 6), (23, 7), (23, 10), (23, 19), (23, 20), (23, 26), (24, 4), (24, 6), (24, 10), (24, 14), (24, 22), (24, 24), (24, 26), (25, 0), (25, 2), (25, 3), (25, 9), (25, 11), (25, 14), (25, 22), (25, 26), (25, 27), (26, 5), (26, 11), (26, 15), (26, 19), (26, 27), (26, 28), (27, 1), (27, 4), (27, 7), (27, 14), (27, 28), (28, 0), (28, 2), (28, 3), (28, 5), (28, 6), (28, 19), (28, 21), (28, 23), (28, 24), (28, 27), (28, 28), (29, 4), (29, 18)]
black_pearls = [(0, 5), (0, 10), (0, 19), (1, 3), (1, 8), (2, 16), (2, 19), (2, 26), (3, 3), (3, 6), (3, 8), (3, 9), (4, 7), (4, 16), (4, 22), (4, 25), (5, 1), (5, 4), (5, 9), (5, 21), (6, 12), (6, 17), (7, 7), (7, 15), (7, 16), (7, 21), (8, 6), (8, 14), (8, 16), (8, 28), (9, 11), (10, 21), (11, 6), (11, 11), (11, 17), (11, 24), (12, 1), (12, 3), (12, 7), (12, 19), (12, 26), (13, 3), (13, 6), (13, 8), (13, 12), (13, 16), (14, 4), (14, 15), (15, 12), (15, 22), (15, 26), (15, 28), (16, 7), (16, 15), (17, 10), (17, 11), (17, 20), (18, 3), (18, 24), (18, 25), (19, 0), (19, 14), (19, 15), (19, 24), (20, 9), (20, 12), (20, 20), (20, 29), (21, 0), (21, 22), (22, 3), (22, 12), (22, 16), (22, 18), (25, 6), (25, 12), (25, 17), (26, 24), (27, 19), (27, 25), (28, 9), (28, 13), (28, 18), (29, 10), (29, 15)]

#一个中等的日挑战
size = 30
white_pearls = [(0, 13), (0, 16), (1, 7), (1, 20), (1, 24), (1, 28), (2, 1), (2, 6), (2, 16), (2, 22), (3, 1), (3, 18), (3, 21), (4, 5), (4, 6), (4, 7), (4, 29), (5, 4), (5, 15), (6, 2), (6, 13), (7, 0), (7, 2), (7, 4), (7, 13), (7, 14), (7, 15), (7, 27), (7, 29), (8, 4), (8, 27), (9, 3), (9, 7), (9, 18), (10, 1), (10, 3), (10, 8), (10, 18), (10, 20), (10, 23), (11, 23), (11, 24), (12, 2), (12, 4), (12, 19), (13, 6), (13, 19), (13, 20), (13, 22), (13, 26), (14, 3), (14, 7), (14, 12), (14, 13), (14, 16), (15, 2), (15, 7), (15, 15), (15, 24), (15, 26), (16, 0), (16, 6), (16, 19), (16, 22), (17, 1), (17, 3), (17, 5), (17, 23), (18, 0), (18, 4), (18, 5), (18, 12), (18, 25), (18, 26), (19, 1), (19, 3), (19, 21), (19, 23), (19, 24), (19, 26), (19, 28), (19, 29), (20, 1), (20, 3), (20, 5), (20, 21), (20, 23), (20, 28), (21, 8), (21, 12), (21, 13), (21, 18), (21, 20), (22, 5), (22, 7), (22, 8), (22, 23), (22, 24), (22, 25), (22, 28), (23, 8), (23, 12), (23, 17), (23, 18), (24, 29), (25, 9), (25, 10), (25, 11), (25, 19), (26, 0), (26, 16), (26, 19), (27, 6), (27, 8), (27, 28), (28, 3), (28, 7), (28, 10), (28, 11), (28, 15), (28, 16), (28, 21), (28, 22), (29, 12), (29, 13), (29, 28)]
black_pearls = [(0, 10), (0, 12), (0, 21), (0, 27), (1, 19), (1, 26), (2, 2), (2, 4), (2, 7), (2, 9), (2, 14), (3, 4), (3, 25), (3, 26), (4, 10), (4, 16), (4, 19), (4, 24), (5, 2), (5, 22), (5, 25), (6, 19), (6, 24), (7, 6), (7, 9), (7, 11), (8, 8), (8, 18), (8, 22), (9, 0), (9, 10), (9, 16), (9, 23), (9, 28), (10, 14), (10, 22), (11, 11), (12, 0), (12, 6), (12, 13), (12, 16), (12, 17), (12, 25), (13, 10), (13, 27), (14, 5), (14, 11), (15, 0), (15, 18), (15, 20), (15, 23), (15, 28), (16, 11), (16, 12), (17, 4), (17, 6), (17, 16), (18, 7), (18, 11), (18, 15), (18, 21), (19, 13), (19, 19), (20, 6), (20, 10), (21, 1), (21, 5), (21, 16), (22, 10), (23, 1), (23, 7), (23, 13), (23, 15), (23, 25), (24, 17), (24, 21), (24, 26), (25, 6), (25, 20), (25, 24), (26, 3), (26, 5), (26, 22), (26, 24), (26, 26), (27, 2), (27, 11), (27, 15), (27, 19), (27, 27), (29, 0), (29, 8), (29, 19), (29, 25)]

#一个困难的周挑战
size = 35
white_pearls = [(0, 5), (0, 8), (0, 13), (0, 17), (0, 23), (0, 25), (0, 29), (1, 0), (1, 1), (1, 5), (1, 17), (1, 19), (1, 24), (1, 31), (2, 6), (2, 7), (2, 10), (2, 16), (2, 26), (2, 29), (3, 6), (3, 11), (3, 15), (3, 18), (3, 29), (3, 30), (3, 32), (4, 3), (4, 23), (4, 26), (4, 31), (5, 3), (5, 5), (5, 13), (5, 18), (5, 26), (5, 31), (6, 1), (6, 2), (6, 30), (6, 32), (6, 33), (7, 2), (7, 5), (7, 7), (7, 26), (7, 32), (8, 6), (8, 10), (8, 13), (8, 24), (8, 27), (8, 32), (9, 16), (9, 21), (9, 24), (9, 32), (10, 12), (10, 13), (10, 19), (10, 21), (10, 26), (10, 29), (10, 30), (11, 10), (11, 15), (11, 22), (11, 23), (12, 7), (12, 9), (12, 11), (12, 14), (12, 25), (12, 27), (12, 28), (12, 31), (13, 1), (13, 3), (13, 6), (13, 9), (13, 16), (13, 17), (13, 23), (13, 30), (13, 32), (14, 2), (14, 6), (14, 10), (14, 14), (14, 20), (14, 27), (14, 28), (14, 34), (15, 1), (15, 9), (15, 10), (15, 21), (15, 23), (15, 28), (15, 30), (16, 2), (16, 4), (16, 6), (16, 16), (16, 27), (17, 7), (17, 9), (17, 14), (17, 16), (17, 20), (17, 30), (18, 1), (18, 6), (18, 7), (18, 11), (18, 14), (18, 15), (18, 18), (18, 20), (18, 23), (18, 25), (18, 28), (19, 6), (19, 8), (19, 9), (19, 12), (19, 20), (19, 22), (19, 26), (19, 28), (20, 0), (20, 5), (20, 7), (20, 15), (20, 17), (20, 18), (20, 24), (20, 25), (20, 29), (20, 32), (21, 6), (21, 8), (21, 14), (21, 27), (22, 4), (22, 13), (22, 18), (22, 29), (23, 2), (23, 6), (23, 13), (23, 15), (23, 21), (23, 23), (23, 27), (23, 28), (23, 29), (23, 33), (24, 7), (24, 9), (24, 13), (24, 17), (24, 20), (24, 22), (24, 27), (24, 34), (25, 2), (25, 22), (26, 9), (26, 15), (26, 20), (26, 22), (26, 31), (27, 5), (27, 8), (27, 10), (27, 15), (27, 22), (27, 34), (28, 14), (28, 16), (28, 18), (28, 23), (28, 25), (28, 26), (28, 27), (28, 30), (29, 17), (29, 19), (29, 21), (29, 26), (29, 32), (30, 1), (30, 4), (30, 9), (30, 24), (30, 29), (31, 3), (31, 6), (31, 10), (31, 11), (31, 17), (31, 25), (32, 3), (32, 15), (32, 17), (32, 20), (32, 23), (32, 24), (32, 26), (33, 4), (33, 12), (33, 13), (33, 14), (33, 15), (33, 17), (33, 27), (33, 30), (34, 16), (34, 26), (34, 29), (34, 30)]
black_pearls = [(0, 3), (0, 27), (1, 15), (1, 34), (2, 11), (2, 20), (2, 25), (3, 13), (3, 20), (4, 0), (4, 8), (4, 11), (4, 34), (5, 6), (5, 14), (5, 16), (5, 22), (5, 30), (6, 10), (6, 15), (6, 23), (6, 29), (7, 4), (7, 9), (7, 18), (7, 22), (8, 11), (8, 16), (8, 19), (8, 21), (8, 29), (9, 5), (9, 18), (9, 22), (9, 28), (10, 1), (10, 28), (11, 6), (11, 8), (11, 17), (11, 33), (12, 0), (12, 4), (12, 13), (12, 19), (13, 12), (13, 22), (14, 25), (14, 33), (15, 19), (15, 24), (15, 26), (16, 14), (16, 18), (16, 32), (17, 11), (17, 12), (17, 23), (19, 2), (19, 5), (19, 18), (19, 29), (21, 3), (21, 19), (21, 21), (21, 23), (21, 25), (21, 33), (22, 8), (22, 10), (22, 15), (24, 11), (24, 18), (24, 29), (24, 31), (25, 3), (25, 5), (25, 10), (25, 17), (25, 25), (26, 4), (26, 7), (26, 25), (26, 29), (27, 12), (27, 14), (27, 18), (27, 32), (28, 7), (28, 12), (29, 0), (29, 2), (29, 6), (29, 29), (30, 11), (30, 13), (30, 19), (30, 27), (30, 34), (31, 2), (31, 34), (32, 22), (33, 2), (33, 5), (33, 8), (33, 9), (34, 24), (34, 32)]

#一个中等的月挑战
size = 40
white_pearls = [(0, 5), (0, 6), (0, 20), (0, 26), (0, 28), (0, 31), (0, 33), (1, 0), (1, 9), (1, 12), (1, 16), (1, 25), (1, 29), (1, 32), (1, 36), (2, 3), (2, 4), (2, 12), (2, 16), (2, 30), (3, 7), (3, 8), (3, 10), (3, 13), (3, 17), (3, 21), (3, 31), (3, 33), (4, 2), (4, 11), (4, 20), (4, 39), (5, 13), (5, 22), (5, 24), (5, 32), (5, 35), (6, 7), (6, 9), (6, 12), (6, 19), (6, 20), (6, 23), (6, 25), (6, 27), (6, 30), (6, 34), (6, 37), (7, 0), (7, 6), (7, 9), (7, 18), (7, 21), (7, 32), (7, 36), (8, 3), (8, 4), (8, 5), (8, 6), (8, 12), (8, 22), (8, 25), (8, 36), (8, 39), (9, 3), (9, 12), (9, 16), (9, 19), (9, 21), (9, 26), (9, 28), (9, 33), (9, 36), (9, 37), (10, 0), (10, 10), (10, 12), (10, 16), (10, 24), (10, 34), (10, 36), (10, 37), (11, 2), (11, 4), (11, 6), (11, 9), (11, 14), (11, 16), (11, 24), (11, 31), (12, 7), (12, 17), (12, 25), (12, 27), (12, 28), (12, 30), (12, 32), (12, 35), (12, 39), (13, 3), (13, 6), (13, 14), (13, 15), (13, 21), (13, 30), (13, 32), (13, 33), (14, 5), (14, 6), (14, 13), (14, 22), (15, 4), (15, 10), (15, 16), (15, 29), (15, 30), (15, 38), (15, 39), (16, 5), (16, 29), (16, 33), (16, 34), (17, 6), (17, 7), (17, 8), (17, 9), (17, 12), (17, 21), (17, 29), (17, 32), (17, 34), (17, 35), (18, 2), (18, 4), (18, 12), (18, 14), (18, 27), (18, 30), (19, 6), (19, 10), (19, 14), (19, 16), (19, 17), (19, 23), (19, 33), (19, 38), (20, 7), (20, 30), (20, 35), (21, 7), (21, 13), (21, 15), (21, 17), (21, 20), (21, 23), (21, 25), (21, 34), (21, 39), (22, 8), (22, 11), (22, 12), (22, 14), (22, 20), (22, 21), (22, 35), (23, 5), (23, 7), (23, 10), (23, 20), (23, 27), (23, 32), (23, 33), (23, 39), (24, 5), (24, 16), (24, 17), (24, 20), (24, 23), (24, 26), (24, 31), (24, 32), (24, 34), (24, 36), (25, 1), (25, 4), (25, 6), (25, 11), (25, 15), (25, 19), (25, 29), (25, 34), (25, 37), (25, 38), (26, 7), (26, 14), (26, 16), (26, 20), (26, 27), (26, 28), (26, 35), (27, 6), (27, 7), (27, 28), (28, 1), (28, 5), (28, 6), (28, 8), (28, 19), (28, 20), (28, 25), (29, 1), (29, 3), (29, 4), (29, 5), (30, 4), (30, 17), (30, 18), (30, 21), (30, 24), (30, 26), (30, 28), (30, 37), (31, 0), (31, 3), (31, 6), (31, 8), (31, 9), (31, 15), (31, 26), (31, 39), (32, 1), (32, 6), (32, 21), (32, 27), (32, 33), (33, 5), (33, 30), (33, 34), (33, 38), (34, 9), (34, 32), (34, 36), (34, 39), (35, 4), (35, 11), (35, 18), (35, 19), (35, 23), (35, 24), (35, 29), (35, 33), (35, 34), (36, 7), (36, 12), (36, 23), (36, 25), (36, 36), (37, 3), (37, 5), (37, 15), (37, 20), (37, 30), (38, 7), (38, 11), (38, 20), (38, 23), (38, 39), (39, 7), (39, 22), (39, 32)]
black_pearls = [(0, 17), (0, 39), (1, 1), (1, 14), (1, 20), (1, 23), (2, 7), (2, 27), (2, 34), (2, 38), (3, 4), (3, 25), (4, 5), (4, 28), (4, 31), (4, 34), (5, 10), (5, 15), (5, 16), (5, 28), (6, 1), (6, 4), (6, 14), (7, 25), (8, 9), (8, 20), (8, 29), (8, 34), (9, 18), (9, 20), (10, 31), (11, 5), (11, 8), (11, 10), (11, 12), (11, 26), (12, 19), (12, 20), (12, 38), (13, 0), (13, 8), (13, 23), (14, 12), (14, 19), (14, 27), (14, 28), (14, 34), (15, 0), (15, 2), (15, 17), (15, 31), (16, 12), (16, 15), (16, 21), (16, 24), (16, 27), (17, 0), (17, 38), (18, 3), (18, 11), (18, 19), (18, 20), (18, 24), (18, 25), (18, 37), (19, 1), (19, 3), (19, 27), (20, 12), (20, 20), (20, 32), (21, 5), (21, 28), (22, 1), (22, 23), (22, 27), (22, 29), (22, 37), (23, 1), (23, 3), (23, 13), (23, 17), (23, 24), (24, 27), (24, 29), (25, 9), (25, 23), (26, 24), (26, 33), (26, 38), (27, 3), (27, 11), (27, 17), (27, 18), (27, 22), (28, 12), (28, 16), (28, 30), (28, 35), (29, 9), (29, 29), (29, 33), (29, 36), (29, 39), (30, 3), (30, 11), (30, 14), (30, 30), (30, 32), (31, 19), (31, 23), (31, 31), (32, 9), (32, 13), (32, 20), (32, 25), (32, 31), (33, 0), (33, 3), (33, 12), (33, 14), (33, 19), (34, 13), (34, 16), (34, 22), (34, 27), (34, 28), (35, 8), (35, 10), (35, 31), (35, 38), (36, 1), (36, 3), (36, 14), (36, 21), (36, 32), (36, 34), (37, 13), (37, 18), (38, 17), (38, 27), (38, 29), (39, 0), (39, 2), (39, 5), (39, 9), (39, 18), (39, 25), (39, 36), (39, 37)]


#size, white_pearls, black_pearls = fetch_masyu('https://cn.puzzle-masyu.com/?size=13')
def main(size,white_pearls,black_pearls):
    #初始化grid，数据结构同数回
    size+=1#原来的size是珍珠的坐标，而现在相当于向右下延申，只需要加1
    grid=Grid([[0]*(size) for _ in range(size)])
    #求解就是大一统的过程
    p=1
    for y, x in product(range(1,size-1), range(1,size-1)):
        grid[y][x]=p
        p+=1

    alter={}

    def find_foreparent(size,grid,alter):
        for i, j in product(range(size), range(size)):
            z=int(grid[i][j])
            b=grid[i][j]-z
            while z in alter:#找祖宗
                b=xor5(b,alter[z][1])
                z=alter[z][0]
            grid[i][j]=z+b
    
    def modify(y:int,x:int,z,b=None,grid=grid,alter=alter,size=size):#最伟大的功能
        if b is None:
            b=z-int(z)
            z=int(z)
        while z in alter:#找祖宗
            b=xor5(b,alter[z][1])
            z=alter[z][0]
        #顺便给现在的格子找祖宗
        check0=int(grid[y][x])
        check1=grid[y][x]-check0
        while check0 in alter:#找祖宗
            check1=xor5(check1,alter[check0][1])
            check0=alter[check0][0]
        if check0==z and check1==b:#重复
            return 0
        if check0==z and check1!=b:#出错！
            print(f'{y}行{x}列{z}区冲突！本来是{check0+check1}，现在是{z+b}')
            show_masyu(size, white_pearls,black_pearls, grid)
            raise SamexButDiffbError("出错！")
        if check0!=z:#合并！
            if z>check0:
                alter[z]=(check0,xor5(b,check1))
            else:
                alter[check0]=(z,xor5(b,check1))
            find_foreparent(size,grid,alter)#每次都运行，完美同步；这个最多触发面积次，性能问题不大
            return 1
        else:
            print('?')
            raise UnknownError('出错！')

    #一次性小结构，不算在effect里
    #相邻黑珍珠，则互相延伸
    for lo in black_pearls:
        if (lo[0]+1,lo[1]) in black_pearls:#下面也是黑珍珠
            #上方黑珍珠向上，下方向下
            lo0,lo1=lo,(lo[0]+1,lo[1])
            for success in [find_diy(*lo0,'up'),find_diy(*lo1,'down')]:
                modify(*success[1],grid[success[0]])
                modify(*success[2],xorint(grid[success[0]]))
                modify(*success[3],xorint(grid[success[0]]))

        if (lo[0],lo[1]+1) in black_pearls:
            #左方黑珍珠向左，右方向右
            lo0,lo1=lo,(lo[0],lo[1]+1)
            for success in [find_diy(*lo0,'left'),find_diy(*lo1,'right')]:
                modify(*success[1],grid[success[0]])
                modify(*success[2],xorint(grid[success[0]]))
                modify(*success[3],xorint(grid[success[0]]))

    #“黑空白白”形
    for y,x in black_pearls:
        for direction,pattern in (('up',((2,0),(3,0))),('down',((-2,0),(-3,0))),('left',((0,2),(0,3))),('right',((0,-2),(0,-3)))):
            lolo=((y+pattern[0][0],x+pattern[0][1]),(y+pattern[1][0],x+pattern[1][1]))
            if 0<=lolo[0][0]<size and 0<=lolo[0][1]<size and 0<=lolo[1][0]<size and 0<=lolo[1][1]<size:
                if lolo[0] in white_pearls and lolo[1] in white_pearls:#黑的向相反方向发动
                    success=find_diy(y,x,direction)
                    modify(*success[1],grid[success[0]])
                    modify(*success[2],xorint(grid[success[0]]))
                    modify(*success[3],xorint(grid[success[0]]))

    #黑珍珠的对角处有相邻白珍珠，则黑珍珠不能往那边伸
    for y,x in black_pearls:
        wh=find_neig8(y,x)
        for i,j,k in ((0,1,'up'),(1,3,'right'),(3,2,'down'),(2,0,'left')):
            if wh[i] in white_pearls and wh[j] in white_pearls:#一面占满，往反面伸
                success=find_diy(y,x,k)
                modify(*success[1],grid[success[0]])
                modify(*success[2],xorint(grid[success[0]]))
                modify(*success[3],xorint(grid[success[0]]))
    effect=1
    #难度不亚于数回，但这次可以复用了
    while effect>0:
        effect=0
        #独特逻辑：黑·白
        #黑：上四格、下四格中恰有一个左右两边不同；左四格、右边四格中恰有一个上下两边不同
        for y,x in black_pearls:
            #若一个方向不满足，则相反方向成立；重复4次
            for direction1,direction2 in (('up','down'),('down','up'),('left','right'),('right','left')):
                check=find_diy(y,x,direction1)
                for i in check:#检查是否有出界项
                    if i[0]<0 or i[0]>=size or i[1]<0 or i[1]>=size:
                        success=find_diy(y,x,direction2)
                        effect+=modify(*success[1],grid[success[0]])
                        effect+=modify(*success[2],xorint(grid[success[0]]))
                        effect+=modify(*success[3],xorint(grid[success[0]]))
                        break
                else:#没有出界项
                    #正常0=1≠2=3，若不满足则对面成立；现在检查是否有反例
                    zu=[grid[i] for i in check]
                    zu1=[zu[0],zu[1],xorint(zu[2]),xorint(zu[3])]
                    #zu[2],zu[3]=xorint(zu[2]),xorint(zu[3])
                    seen=set(zu1)
                    for i in seen:
                        if xorint(i) in seen:#不成立！
                            success=find_diy(y,x,direction2)
                            effect+=modify(*success[1],grid[success[0]])
                            effect+=modify(*success[2],xorint(grid[success[0]]))
                            effect+=modify(*success[3],xorint(grid[success[0]]))
                            break
            #此外黑周围四格还固定是一个L字形，所以tian也可用
            check=find_diy(y,x,'tian')#不会出界
            for i,j in {(0,1):(2,3),(1,3):(0,2),(3,2):(0,1),(2,0):(1,3)}.items():
                if grid[check[i[0]]]==xorint(grid[check[i[1]]]):
                    effect+=modify(*check[j[0]],grid[check[j[1]]])
        #白：周围四格对角不同；确定方向后各延伸一格，不能形成八格对立
        for y,x in white_pearls:
            check=find_diy(y,x,'tian')#不会出界
            #对角不同，这已经包含水平垂直了
            effect+=modify(*check[3],xorint(grid[check[0]]))
            effect+=modify(*check[2],xorint(grid[check[1]]))
            #考虑延申，这包含了三连白
            for lkasdj in ('v','h'):
                check=find_diy(y,x,lkasdj)
                ppp=0
                for i in check:
                    if i[0]<0 or i[0]>=size or i[1]<0 or i[1]>=size:
                        ppp=1
                if ppp:#出界了
                    continue
                checkzhi=[grid[i] for i in check]
                intlist=set(map(lambda x:int(x),checkzhi))
                if len(intlist)==2:#唯一一个可以处理的东西
                    #逐个尝试相等和不等，如果有一个造成了致命结构，就采用另一个
                    intlist=tuple(intlist)
                    for zhi in (0,0.5):
                        temp=[]
                        for i in check:
                            if int(grid[i])==intlist[1]:
                                temp.append(xor5(zhi,grid[i]-int(grid[i])))
                            else:
                                temp.append(grid[i]-int(grid[i]))
                        if temp==[0,0.5]*4 or temp==[0.5,0]*4:#发现了致命结构！
                            #这里比较特殊，是纯粹的两个数的合并，调用modify有点费劲
                            #找到一个采用intlist0的格子，必定存在
                            location=(999,999)
                            for i in check:
                                if int(grid[i])==intlist[0]:
                                    location=i
                                    break
                            effect+=modify(*i,intlist[1],xor5(grid[i]-int(grid[i]),0.5-zhi))
                #推论：若前六个满足，则七八相同；后六个满足，则一二相同
                if checkzhi[0]==checkzhi[2]==checkzhi[4] and checkzhi[1]==checkzhi[3]==checkzhi[5] and checkzhi[0]==xorint(checkzhi[1]):
                    effect+=modify(*check[6],checkzhi[7])
                if checkzhi[6]==checkzhi[2]==checkzhi[4] and checkzhi[7]==checkzhi[3]==checkzhi[5] and checkzhi[7]==xorint(checkzhi[6]):
                    effect+=modify(*check[0],checkzhi[1])
        #小结构
        #最强的小结构，依旧禁止国际棋盘
        for y, x in product(range(1,size-1), range(1,size-1)):
            tian=((y,x),(y+1,x),(y+1,x+1),(y,x+1))#本，下，右下，右
            tianlist=[grid[temp] for temp in tian]
            tianintlist=set(map(lambda x:int(x),tianlist))
            if len(tianintlist)==1:#统一了，没你事了
                continue
            if tianlist[0]==tianlist[2]:#根据tian硬编码了，但记住这是左上右下对角相等
                if int(tianlist[1])==int(tianlist[0]) and tianlist[1]!=tianlist[0]:#危险，tianlist[3]必须挽回
                    effect+=modify(*tian[3],tianlist[0])
                if int(tianlist[3])==int(tianlist[0]) and tianlist[3]!=tianlist[0]:#同样，tianlist[1]必须挽回
                    effect+=modify(*tian[1],tianlist[0])
                
            if tianlist[1]==tianlist[3]:#根据tian硬编码了，但记住这是右上左下对角相等
                if int(tianlist[0])==int(tianlist[1]) and tianlist[0]!=tianlist[1]:#危险，tianlist[2]必须挽回
                    effect+=modify(*tian[2],tianlist[1])
                if int(tianlist[2])==int(tianlist[1]) and tianlist[2]!=tianlist[1]:#同样，tianlist[0]必须挽回
                    effect+=modify(*tian[0],tianlist[1])
            #特殊的来了，上俩相异下俩相异
            if tianlist[0]==xorint(tianlist[1]) and tianlist[2]==xorint(tianlist[3]):
                effect+=modify(*tian[0],tianlist[3])
            if tianlist[0]==xorint(tianlist[3]) and tianlist[2]==xorint(tianlist[1]):
                effect+=modify(*tian[0],tianlist[1])

        '''
        不同+双白；可泛化成单白：
        1.0 1.5 
        2.0 3.0 
        3.5 2.5 
        2.0 3.0 
        其中白在中间，则2=3.这比认双白要泛化
        还有一种：
        1.0 1.5
        xx
        xx
        2.0 2.5
        则中间也变成水平
        水平结构同理：
        1.0 [2.0] 3.5 2.0
        1.5  3.0  2.5 3.0
        '''
        for y,x in white_pearls:
            if y<=size-3 and grid[y][x]!=grid[y][x+1]:
                check=find_diy(y,x,[(-1,0),(-1,1),(0,0),(0,1),(1,0),(1,1),(2,0),(2,1)])
                checkzhi=[grid[i] for i in check]
                if checkzhi[0]==xorint(checkzhi[1]) and checkzhi[2]==xorint(checkzhi[5])==checkzhi[6] and checkzhi[3]==xorint(checkzhi[4])==checkzhi[7]:
                    effect+=modify(y,x,checkzhi[3])
                if checkzhi[6]==xorint(checkzhi[7]) and xorint(checkzhi[2])==checkzhi[5]==checkzhi[1] and xorint(checkzhi[3])==checkzhi[4]==checkzhi[0]:
                    effect+=modify(y,x,checkzhi[3])
                if checkzhi[0]==xorint(checkzhi[1]) and checkzhi[6]==xorint(checkzhi[7]):
                    effect+=modify(y,x,checkzhi[3])
            if x<=size-3 and grid[y][x]!=grid[y+1][x]:
                check=find_diy(y,x,[(0,-1),(1,-1),(0,0),(1,0),(0,1),(1,1),(0,2),(1,2)])
                checkzhi=[grid[i] for i in check]
                if checkzhi[0]==xorint(checkzhi[1]) and checkzhi[2]==xorint(checkzhi[5])==checkzhi[6] and checkzhi[3]==xorint(checkzhi[4])==checkzhi[7]:
                    effect+=modify(y,x,checkzhi[3])
                if checkzhi[6]==xorint(checkzhi[7]) and xorint(checkzhi[2])==checkzhi[5]==checkzhi[1] and xorint(checkzhi[3])==checkzhi[4]==checkzhi[0]:
                    effect+=modify(y,x,checkzhi[3])
                if checkzhi[0]==xorint(checkzhi[1]) and checkzhi[6]==xorint(checkzhi[7]):
                    effect+=modify(y,x,checkzhi[3])



        #连通性部分
        liantong4=[]
        #1、现有格子加入liantong系列
        visited=set()
        for y, x in product(range(size), range(size)):
            if (y,x) not in visited:
                zu=grid[y][x]
                now=[set(),set(),zu]#内部，边界，族
                boundry=set()
                boundry.add((y,x))
                while boundry:
                    lo=boundry.pop()
                    if grid[lo[0]][lo[1]]!=zu:
                        now[1].add(lo)
                    else:
                        now[0].add(lo)
                        boundry.update(set([i for i in find_neig4(*lo) if i not in now[0] and 0<=i[0]<size and 0<=i[1]<size]))
                visited.update(now[0])
                liantong4.append(now)

        '''
        冲破封锁：
        若去掉本体和边界后，其他部分至少有一对相反的东西（在绝大部分时候这很容易被满足，但最后阶段不是的）：
        1、外界只有一些相反和一些相同的未知，则这些未知被同化（最主要）
        2、外界全部独立相同，被同化；
        3、外界全部相反，报错
        '''
        for inter,outer,zu in liantong4:
            kind=set(map(lambda x:grid[x],outer))
            if len(kind)>2:#太杂了
                continue
            if len(kind)==1 and next(iter(kind))!=zu:#外界全同？
                #检查去掉本体和边界后，是否至少有一对相反内容
                jiancha=set()
                for y, x in product(range(size), range(size)):
                    if (y,x) not in inter and (y,x) not in outer:
                        if xorint(grid[y][x]) in jiancha:#成功找到
                            effect+=modify(next(iter(inter))[0],next(iter(inter))[1],next(iter(kind)))
                            break
                        else:
                            jiancha.add(grid[y][x])
                
            else:#len==2，触发规则1，查看是否有一个是相反；是的话就go
                if int(zu) in map(lambda x:int(x),kind):#有！那另一个就直接同化
                    #找到另一个的坐标
                    situation=None#故技重施
                    for j in outer:#j是外围的每一个坐标
                        if grid[j]!=xorint(zu):
                            situation=j
                            break
                    if situation is not None:
                        #检查去掉本体和边界后，是否至少有一对相反内容
                        jiancha=set()
                        for y, x in product(range(size), range(size)):
                            if (y,x) not in inter and (y,x) not in outer:
                                if xorint(grid[y][x]) in jiancha:#成功找到
                                    effect+=modify(situation[0],situation[1],zu)
                                    break
                                else:
                                    jiancha.add(grid[y][x])
                        
                        
                    else:
                        raise UnknownError('未知错误！')
        '''
        防止闭合：
        只考察0，把所有0去掉后剩余格子显然应该连通
        若将剩余非0.5格子中去掉一个，不再连通，说明这个去掉的格子是重要的枢纽格，只能是0.5
        由于代价过大，仅当前面都推不动时使用
        '''
        if effect==0:
            #生成所有除0以外格子集合
            gezi_except_0=set()
            for y, x in product(range(size), range(size)):
                if grid[y][x]!=0:
                    gezi_except_0.add((y,x))
            for i in gezi_except_0:#遍历每一个0.5以外元素，i是禁忌元素
                if grid[i[0]][i[1]]==0.5:
                    continue

                # 剪枝 1：有效邻居太少的不可能是割点
                ne_valid = [nb for nb in find_neig4(*i) if nb in gezi_except_0]
                if len(ne_valid) <= 1:
                    continue
                # 找到起点 (避开被抠掉的 i)
                start = ne_valid[0]

                # 剪枝 2：快速测试它的几个邻居之间能否绕开 i 互相连通
                stack = [start]
                flood = {start}
                while stack:
                    curr = stack.pop()
                    for j in find_neig4(*curr):
                        if j in gezi_except_0 and j not in flood and j != i:
                            flood.add(j)
                            stack.append(j)
                if len(flood)<len(gezi_except_0)-1:
                    effect+=modify(i[0],i[1],0.5)
                    break#我也不知道怎么回事，但是不加这个break就会出错

                    
        print(effect)

    #珍珠位于其坐标的右下角，即珍珠(y,x)在(y,x) (y,x+1) (y+1,x) (y+1,x+1)四个格子中间


    #只出现一次的区消失
    p={}
    for y, x in product(range(size), range(size)):
        z=int(grid[y][x])
        if z not in p:
            p[z]=1
        else:
            p[z]+=1
    for y, x in product(range(size), range(size)):
        z=int(grid[y][x])
        if p[z]==1:
            grid[y][x]=-1

    #把现有的区块按顺序重新命名，防止配色意外重合导致看不清
    endalter={}
    pointer=1
    for y, x in product(range(size), range(size)):
        z=int(grid[y][x])
        if z not in (-1,0) and z not in endalter:
            endalter[z]=pointer
            pointer+=1
    for y, x in product(range(size), range(size)):
        z=int(grid[y][x])
        if z not in (-1,0):
            grid[y][x]=endalter[z]+grid[y][x]-z


    #把东西都变回去，事实上变完之后坐标偏移，使得珍珠位于其坐标的左上角了
    size-=2
    grid=[grid[i][1:size+1] for i in range(1,size+1)]
    return grid


grid=main(size,white_pearls,black_pearls)
#理论上最后应该画线，但懒得画了
show_masyu(size, white_pearls,black_pearls, grid)