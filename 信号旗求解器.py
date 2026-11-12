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

from playwright.sync_api import sync_playwright

def fetch_shingoki(url="https://www.puzzle-shingoki.com/"):
    """
    输入信号旗网页链接（支持每日、每周、每月等任意尺寸页面），
    后台静默抓取并直接返回 (size, white_circles, black_circles)
    - size: 正方形尺寸 (int)
    - white_circles: 白圈元组列表 [(r, c, num), ...]
    - black_circles: 黑圈元组列表 [(r, c, num), ...]
    """
    print(f"正在后台启动无头浏览器抓取信号旗页面: {url} ...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        # 核心等待：等棋盘所有顶点渲染就绪
        page.wait_for_selector(".loop-dot")

        data = page.evaluate("""() => {
            let dots = Array.from(document.querySelectorAll('.loop-dot'));

            function getPx(el, prop) {
                let val = el.style[prop];
                if (val && val.includes('px')) return parseFloat(val);
                return el.getBoundingClientRect()[prop === 'top' ? 'top' : 'left'];
            }

            function cluster(values) {
                values.sort((a, b) => a - b);
                let res = [];
                values.forEach(v => {
                    if (!res.some(existing => Math.abs(existing - v) < 5)) {
                        res.push(v);
                    }
                });
                return res.sort((a, b) => a - b);
            }

            let allY = dots.map(d => getPx(d, 'top'));
            let allX = dots.map(d => getPx(d, 'left'));

            let uniqueY = cluster(allY);
            let uniqueX = cluster(allX);
            let size = uniqueY.length;

            function getIndex(val, arr) {
                let bestIdx = 0, minDiff = 999999;
                for (let i = 0; i < arr.length; i++) {
                    let diff = Math.abs(val - arr[i]);
                    if (diff < minDiff) {
                        minDiff = diff;
                        bestIdx = i;
                    }
                }
                return bestIdx;
            }

            let white_circles = [];
            let black_circles = [];

            dots.forEach(el => {
                let isWhite = el.classList.contains('dot-white');
                let isBlack = el.classList.contains('dot-black');

                if (isWhite || isBlack) {
                    let y_px = getPx(el, 'top');
                    let x_px = getPx(el, 'left');

                    let r = getIndex(y_px, uniqueY);
                    let c = getIndex(x_px, uniqueX);

                    let span = el.querySelector('span') || el;
                    let txt = span ? span.innerText.trim() : "";
                    let num = (txt !== "" && !isNaN(txt)) ? parseInt(txt) : 0;

                    if (isWhite) {
                        white_circles.push([r, c, num]);
                    } else {
                        black_circles.push([r, c, num]);
                    }
                }
            });

            return {
                size: size,
                white_circles: white_circles,
                black_circles: black_circles
            };
        }""")

        browser.close()

        white_circles = [tuple(p) for p in data["white_circles"]]
        black_circles = [tuple(p) for p in data["black_circles"]]

        print(f"✔ 抓取成功！尺寸: {data['size']}x{data['size']} (白圈: {len(white_circles)}, 黑圈: {len(black_circles)})")
        return data["size"], white_circles, black_circles

def show_shingoki(size, white_circles, black_circles, grid):
    """
    信号旗 (Shingoki) 终极拓扑对偶染色看板
    - 支持白圈黑字、黑圈白字数字居中渲染
    - 自动识别 grid 是否带有外围海洋，圆圈永不错位！
    - 支持鼠标任意键自由拖拽平移画布、滚轮防爆屏
    """
    root = tk.Tk()
    root.title("Shingoki (Traffic Lights) Dual-Coloring Solver - [按住鼠标任意键可自由拖动画布]")

    # 1. 核心自适应：自动检测 grid 是否还带着外层 0 号海洋层
    grid_h = len(grid)
    grid_w = len(grid[0])
    all_circles = white_circles + black_circles
    max_p_coord = max([max(p[0], p[1]) for p in all_circles] or [0])

    # 如果 grid 尺寸大于圆圈最大坐标 + 1，说明外围海洋还在！
    has_ocean = (grid_h > max_p_coord + 1)
    offset = 1 if has_ocean else 0

    # 2. 屏幕防爆自适应尺寸
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()

    cell_size = max(28, min(48, 800 // max(grid_w, grid_h)))
    margin_x = 50
    margin_y = 50

    total_w = margin_x * 2 + cell_size * grid_w
    total_h = margin_y * 2 + cell_size * grid_h

    view_w = min(total_w + 30, int(screen_w * 0.82))
    view_h = min(total_h + 30, int(screen_h * 0.82))
    root.geometry(f"{view_w}x{view_h}+{(screen_w - view_w)//2}+{(screen_h - view_h)//2}")

    # 3. 带漫游平移能力的画布系统
    frame = tk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(frame, bg="#2B2B2B", scrollregion=(0, 0, total_w, total_h))
    h_bar = tk.Scrollbar(frame, orient=tk.HORIZONTAL, command=canvas.xview)
    v_bar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
    canvas.configure(xscrollcommand=h_bar.set, yscrollcommand=v_bar.set)

    h_bar.pack(side=tk.BOTTOM, fill=tk.X)
    v_bar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # 鼠标拖拽平移漫游
    for btn in ("<ButtonPress-1>", "<ButtonPress-2>", "<ButtonPress-3>"):
        canvas.bind(btn, lambda e: canvas.scan_mark(e.x, e.y))
    for motion in ("<B1-Motion>", "<B2-Motion>", "<B3-Motion>"):
        canvas.bind(motion, lambda e: canvas.scan_dragto(e.x, e.y, gain=1))
    canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
    canvas.bind("<Shift-MouseWheel>", lambda e: canvas.xview_scroll(int(-1 * (e.delta / 120)), "units"))

    # 4. 配色生成函数 (继承经典的 x.0 / x.5 方案)
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

    # 6. 绘制所有晶格点与信号圈 (居中咬合在十字交点上)
    dot_r = max(2, cell_size // 14)
    circle_r = cell_size * 0.35  # 略微加大半径以容纳清晰数字
    font_num = ("Arial", max(9, int(cell_size * 0.36)), "bold")

    # 绘制背景小晶格黑点
    for r in range(grid_h + 1):
        for c in range(grid_w + 1):
            px = margin_x + c * cell_size
            py = margin_y + r * cell_size
            canvas.create_oval(px - dot_r, py - dot_r, px + dot_r, py + dot_r, fill="#555555", outline="")

    # 绘制白圈 (White Circles: 白底黑字，直行)
    for p in white_circles:
        pr, pc = p[0], p[1]
        num_str = str(p[2]) if len(p) > 2 else ""
        cx = margin_x + (pc + offset) * cell_size
        cy = margin_y + (pr + offset) * cell_size

        # 白圈圆形主体
        canvas.create_oval(cx - circle_r, cy - circle_r, cx + circle_r, cy + circle_r,
                           fill="#FFFFFF", outline="#000000", width=2.5)
        # 居中黑字
        if num_str:
            canvas.create_text(cx, cy, text=num_str, font=font_num, fill="#000000")

    # 绘制黑圈 (Black Circles: 黑底白字，转弯)
    for p in black_circles:
        pr, pc = p[0], p[1]
        num_str = str(p[2]) if len(p) > 2 else ""
        cx = margin_x + (pc + offset) * cell_size
        cy = margin_y + (pr + offset) * cell_size

        # 黑圈圆形主体
        canvas.create_oval(cx - circle_r, cy - circle_r, cx + circle_r, cy + circle_r,
                           fill="#111111", outline="#000000", width=2.5)
        # 居中白字
        if num_str:
            canvas.create_text(cx, cy, text=num_str, font=font_num, fill="#FFFFFF")

    root.mainloop()

def find_neig4(i,j):#保留旧类型，虽然可以被兼容，但这个更快啊
    return [(i+1,j),(i-1,j),(i,j+1),(i,j-1)]

def find_neig8(i,j):#注意是斜角，不是8相邻
    return [(i+1,j+1),(i+1,j-1),(i-1,j+1),(i-1,j-1)]

def find_diy(i,j,kind):#find的集大成者，改过了
    match kind:
        case ('tian',_):#田，顺序为本-右-下-右下
            return [(i,j),(i,j+1),(i+1,j),(i+1,j+1)]
        case 'v':#指白珍珠往竖直方向延申，共8格；致命结构是0=1≠2=3≠4……
            return [(i-1,j),(i-1,j+1),(i,j),(i,j+1),(i+1,j),(i+1,j+1),(i+2,j),(i+2,j+1)]
        case 'h':#指白珍珠往水平方向延申，共8格
            return [(i,j-1),(i+1,j-1),(i,j),(i+1,j),(i,j+1),(i+1,j+1),(i,j+2),(i+1,j+2)]
        case ('up',x):#以下四个是步长对应的两格；
            return [(i+1-x,j),(i+1-x,j+1)]
        case ('down',x):
            return [(i+x,j),(i+x,j+1)]
        case ('left',x):
            return [(i,j+1-x),(i+1,j+1-x)]
        case ('right',x):
            return [(i,j+x),(i+1,j+x)]
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

#日
size = 31
white_circles = [(0, 7, 6), (0, 15, 15), (1, 3, 2), (1, 8, 2), (1, 11, 2), (1, 25, 10), (2, 17, 2), (2, 18, 3), (2, 20, 2), (2, 25, 5), (3, 9, 3), (3, 15, 3), (3, 27, 5), (4, 7, 2), (5, 2, 4), (5, 8, 3), (5, 18, 2), (6, 1, 2), (6, 4, 2), (6, 12, 3), (6, 23, 2), (7, 26, 2), (7, 29, 3), (8, 23, 2), (8, 25, 2), (8, 30, 3), (9, 4, 2), (9, 12, 3), (9, 16, 3), (9, 19, 2), (9, 26, 2), (10, 5, 2), (10, 8, 2), (10, 21, 3), (11, 0, 4), (11, 2, 2), (11, 7, 3), (11, 12, 3), (11, 22, 2), (12, 1, 2), (12, 9, 6), (13, 5, 3), (13, 8, 3), (13, 10, 5), (13, 19, 3), (13, 25, 4), (14, 5, 2), (14, 15, 2), (16, 18, 2), (16, 19, 5), (16, 25, 5), (17, 21, 3), (17, 26, 2), (18, 3, 7), (19, 4, 2), (19, 7, 2), (19, 18, 2), (20, 12, 2), (20, 14, 2), (20, 25, 2), (21, 3, 3), (21, 10, 3), (21, 20, 4), (21, 28, 9), (22, 19, 2), (23, 17, 2), (23, 21, 5), (23, 29, 10), (24, 9, 2), (24, 11, 2), (24, 23, 3), (25, 5, 3), (25, 10, 2), (25, 13, 3), (25, 27, 3), (26, 18, 2), (26, 24, 7), (26, 25, 5), (27, 3, 3), (27, 22, 2), (28, 0, 3), (28, 5, 5), (28, 8, 2), (29, 23, 2), (29, 25, 2), (30, 19, 3), (30, 28, 3)]
black_circles = [(0, 5, 5), (1, 1, 2), (1, 10, 3), (1, 13, 2), (1, 15, 3), (1, 30, 2), (2, 1, 2), (2, 3, 3), (2, 6, 3), (2, 21, 4), (3, 2, 2), (3, 6, 3), (3, 10, 3), (3, 20, 3), (3, 22, 2), (4, 26, 2), (4, 27, 2), (4, 28, 3), (5, 7, 2), (5, 12, 4), (5, 20, 5), (5, 29, 2), (6, 5, 4), (6, 11, 4), (6, 14, 4), (6, 16, 4), (6, 21, 2), (6, 25, 2), (7, 0, 2), (7, 1, 2), (7, 7, 2), (7, 10, 3), (7, 13, 3), (7, 24, 2), (8, 2, 3), (8, 14, 2), (8, 18, 4), (8, 19, 3), (9, 5, 3), (9, 11, 3), (9, 22, 2), (10, 14, 2), (10, 25, 2), (10, 27, 2), (10, 29, 3), (11, 11, 4), (11, 16, 2), (11, 24, 2), (11, 27, 6), (12, 3, 2), (12, 4, 3), (12, 6, 2), (12, 7, 4), (12, 16, 6), (12, 21, 3), (12, 30, 3), (14, 0, 3), (14, 4, 3), (14, 11, 4), (14, 13, 5), (14, 18, 4), (14, 19, 5), (14, 22, 3), (14, 23, 2), (15, 12, 5), (15, 19, 6), (15, 20, 5), (15, 25, 7), (16, 6, 3), (16, 7, 2), (16, 8, 2), (16, 22, 2), (16, 24, 6), (17, 13, 4), (17, 30, 5), (18, 5, 2), (18, 11, 3), (18, 14, 2), (18, 15, 5), (18, 16, 6), (18, 18, 3), (18, 24, 2), (18, 30, 14), (19, 1, 3), (19, 10, 2), (19, 12, 3), (19, 25, 5), (19, 29, 12), (20, 2, 7), (20, 5, 5), (20, 10, 4), (20, 22, 5), (20, 27, 3), (21, 1, 4), (21, 8, 2), (21, 11, 3), (21, 13, 2), (21, 17, 2), (21, 19, 3), (21, 24, 2), (22, 0, 5), (22, 15, 7), (22, 27, 5), (23, 4, 3), (23, 13, 5), (23, 18, 2), (23, 22, 4), (24, 5, 6), (24, 6, 6), (24, 7, 5), (24, 12, 4), (24, 16, 2), (25, 1, 5), (25, 3, 3), (25, 14, 2), (25, 15, 2), (25, 20, 6), (25, 21, 5), (26, 0, 6), (26, 11, 2), (27, 7, 3), (27, 9, 2), (27, 12, 2), (27, 13, 2), (27, 27, 4), (28, 11, 3), (28, 13, 6), (29, 1, 6), (29, 10, 3), (29, 17, 2), (29, 20, 3), (29, 22, 2), (30, 7, 3), (30, 14, 2), (30, 15, 2)]

#周
size = 36
white_circles = [(0, 10, 10), (0, 17, 11), (0, 22, 11), (0, 33, 3), (1, 2, 4), (1, 9, 3), (2, 34, 6), (3, 8, 6), (3, 11, 3), (3, 32, 2), (3, 35, 8), (4, 5, 2), (4, 18, 2), (4, 25, 4), (5, 12, 2), (5, 14, 3), (5, 30, 2), (5, 31, 5), (6, 4, 3), (6, 6, 2), (6, 10, 3), (6, 23, 4), (7, 2, 3), (8, 4, 3), (8, 21, 3), (8, 26, 3), (9, 7, 4), (9, 18, 2), (9, 29, 2), (10, 1, 3), (10, 6, 3), (11, 3, 7), (11, 18, 3), (12, 25, 2), (12, 26, 7), (13, 0, 2), (13, 7, 2), (13, 28, 2), (14, 2, 3), (14, 9, 4), (15, 33, 2), (16, 9, 2), (16, 11, 5), (16, 15, 4), (16, 16, 3), (16, 25, 3), (16, 27, 3), (16, 28, 3), (16, 30, 4), (16, 34, 3), (17, 8, 3), (17, 14, 7), (18, 12, 7), (18, 18, 3), (19, 0, 3), (19, 11, 5), (19, 13, 10), (19, 33, 3), (20, 2, 2), (20, 20, 2), (20, 28, 2), (21, 5, 3), (21, 9, 3), (21, 15, 2), (21, 19, 3), (22, 17, 2), (23, 13, 2), (23, 20, 3), (24, 11, 2), (24, 13, 2), (24, 29, 3), (25, 2, 2), (25, 31, 4), (25, 32, 3), (26, 10, 2), (26, 12, 6), (26, 22, 2), (26, 27, 3), (26, 32, 3), (27, 2, 2), (27, 11, 2), (27, 16, 3), (27, 23, 3), (27, 28, 2), (28, 0, 3), (28, 17, 2), (28, 18, 6), (28, 22, 3), (28, 26, 3), (28, 27, 2), (28, 35, 9), (29, 5, 4), (29, 7, 2), (29, 10, 2), (29, 25, 3), (29, 29, 3), (30, 4, 3), (30, 6, 2), (30, 19, 4), (30, 30, 3), (32, 3, 2), (32, 6, 2), (32, 33, 2), (33, 0, 5), (33, 2, 2), (33, 11, 4), (33, 26, 4), (33, 31, 3), (33, 35, 5), (34, 1, 3), (34, 20, 3), (34, 30, 4), (35, 24, 2)]
black_circles = [(0, 28, 2), (1, 1, 3), (1, 7, 2), (1, 13, 2), (1, 20, 4), (1, 21, 2), (1, 23, 4), (1, 30, 2), (2, 5, 2), (2, 11, 2), (2, 14, 3), (2, 16, 3), (3, 24, 5), (3, 27, 3), (4, 3, 2), (4, 8, 2), (4, 9, 2), (4, 11, 2), (4, 14, 3), (4, 15, 5), (4, 17, 5), (4, 21, 3), (4, 23, 2), (4, 26, 5), (4, 29, 2), (5, 2, 4), (5, 20, 3), (5, 23, 6), (5, 32, 3), (6, 1, 3), (6, 8, 2), (6, 9, 2), (6, 20, 3), (7, 1, 2), (7, 5, 2), (7, 11, 4), (7, 17, 5), (7, 28, 2), (7, 29, 3), (7, 30, 3), (8, 0, 2), (8, 13, 4), (8, 14, 3), (8, 16, 5), (8, 25, 2), (8, 29, 3), (8, 31, 2), (8, 32, 2), (8, 33, 2), (8, 35, 9), (9, 10, 2), (9, 14, 5), (9, 21, 3), (9, 28, 3), (10, 4, 4), (10, 12, 4), (10, 21, 2), (10, 25, 2), (10, 34, 2), (11, 6, 2), (11, 7, 2), (11, 9, 2), (11, 31, 2), (11, 34, 2), (11, 35, 3), (12, 2, 3), (12, 7, 3), (12, 18, 5), (12, 19, 3), (12, 28, 2), (12, 29, 3), (13, 4, 2), (13, 9, 2), (13, 11, 5), (13, 21, 3), (13, 22, 5), (13, 24, 2), (13, 30, 4), (13, 33, 2), (14, 4, 5), (14, 18, 2), (14, 21, 2), (14, 25, 6), (15, 6, 3), (15, 19, 2), (15, 30, 4), (15, 35, 2), (16, 1, 2), (16, 5, 2), (16, 22, 2), (17, 1, 2), (17, 2, 3), (17, 15, 5), (17, 17, 6), (17, 21, 2), (17, 33, 5), (18, 4, 5), (18, 22, 2), (18, 24, 2), (19, 3, 2), (19, 7, 3), (19, 25, 3), (19, 26, 2), (19, 30, 4), (20, 8, 3), (20, 10, 3), (20, 14, 3), (20, 16, 4), (20, 17, 4), (20, 21, 3), (20, 31, 5), (21, 4, 5), (21, 6, 3), (21, 7, 2), (21, 12, 8), (21, 28, 4), (21, 29, 3), (21, 34, 5), (22, 6, 4), (22, 16, 3), (22, 21, 2), (22, 22, 2), (22, 25, 3), (22, 29, 3), (22, 31, 2), (22, 33, 2), (23, 1, 4), (23, 2, 2), (23, 7, 2), (23, 9, 3), (23, 17, 4), (23, 24, 3), (24, 4, 4), (24, 16, 2), (24, 19, 2), (24, 21, 4), (24, 26, 3), (25, 4, 3), (25, 9, 2), (25, 15, 3), (25, 21, 3), (25, 25, 5), (26, 17, 8), (26, 23, 2), (26, 24, 3), (26, 28, 5), (27, 1, 3), (27, 10, 3), (27, 12, 2), (27, 30, 4), (27, 31, 5), (28, 7, 2), (28, 25, 4), (29, 8, 3), (30, 3, 2), (30, 14, 3), (30, 24, 7), (30, 27, 2), (30, 32, 4), (31, 1, 2), (31, 20, 4), (31, 22, 2), (31, 23, 5), (31, 33, 3), (32, 7, 2), (32, 11, 5), (32, 15, 4), (32, 17, 4), (32, 27, 4), (32, 29, 5), (32, 34, 5), (33, 9, 3), (33, 10, 7), (33, 14, 5), (33, 21, 2), (33, 33, 3), (34, 6, 3), (34, 7, 10), (34, 19, 4), (35, 7, 11), (35, 22, 5), (35, 35, 6)]

#月
size = 41
white_circles = [(0, 2, 6), (0, 16, 3), (0, 24, 6), (0, 37, 2), (1, 0, 8), (1, 8, 3), (1, 21, 3), (1, 25, 4), (2, 4, 3), (2, 7, 3), (2, 11, 3), (2, 15, 2), (2, 37, 5), (2, 38, 8), (3, 3, 3), (3, 11, 3), (3, 20, 4), (3, 29, 5), (3, 31, 2), (3, 39, 8), (3, 40, 9), (4, 5, 2), (4, 26, 3), (5, 10, 3), (5, 14, 2), (7, 1, 2), (7, 5, 3), (7, 13, 2), (7, 17, 2), (7, 22, 4), (7, 25, 5), (7, 29, 2), (8, 16, 2), (9, 4, 5), (9, 6, 4), (9, 9, 3), (9, 21, 2), (9, 30, 3), (10, 4, 2), (10, 8, 3), (10, 15, 2), (10, 30, 4), (11, 1, 2), (11, 14, 3), (11, 29, 3), (11, 36, 2), (11, 39, 2), (12, 1, 3), (12, 10, 3), (12, 15, 3), (12, 22, 3), (12, 26, 2), (12, 31, 2), (13, 5, 5), (13, 14, 7), (13, 17, 3), (13, 24, 2), (14, 9, 3), (14, 13, 3), (14, 28, 6), (14, 38, 2), (15, 10, 6), (15, 26, 4), (16, 27, 4), (16, 30, 3), (16, 34, 2), (17, 18, 2), (18, 14, 7), (18, 18, 4), (18, 20, 4), (18, 33, 3), (18, 39, 6), (19, 23, 2), (20, 16, 4), (20, 24, 2), (20, 28, 4), (21, 7, 4), (21, 11, 3), (21, 22, 3), (21, 27, 4), (21, 29, 3), (22, 8, 5), (22, 14, 2), (23, 4, 6), (23, 9, 6), (23, 33, 3), (24, 17, 5), (24, 36, 2), (24, 39, 2), (24, 40, 25), (25, 31, 3), (26, 2, 5), (26, 27, 5), (26, 36, 2), (27, 1, 3), (27, 7, 3), (27, 16, 2), (27, 20, 8), (27, 28, 4), (28, 10, 3), (28, 26, 2), (28, 28, 2), (29, 12, 2), (29, 22, 5), (30, 6, 7), (30, 13, 2), (30, 32, 7), (30, 36, 3), (31, 5, 8), (31, 12, 3), (31, 14, 4), (31, 21, 3), (31, 24, 2), (32, 9, 4), (32, 37, 2), (33, 14, 5), (33, 21, 7), (34, 8, 2), (34, 11, 5), (34, 17, 4), (34, 24, 4), (35, 1, 2), (35, 12, 5), (35, 27, 2), (35, 32, 3), (36, 7, 7), (36, 12, 7), (36, 19, 2), (36, 30, 2), (36, 36, 2), (37, 3, 3), (37, 13, 5), (37, 23, 2), (37, 35, 2), (38, 0, 7), (38, 15, 3), (38, 25, 2), (38, 31, 3), (38, 38, 5), (39, 8, 2), (39, 34, 3), (40, 1, 5), (40, 13, 8)]
black_circles = [(0, 9, 6), (0, 15, 4), (0, 30, 3), (1, 1, 6), (1, 20, 2), (1, 22, 2), (1, 32, 2), (2, 8, 5), (2, 25, 2), (2, 31, 2), (2, 33, 3), (2, 35, 2), (3, 9, 6), (3, 17, 3), (3, 36, 3), (4, 6, 3), (4, 16, 4), (4, 19, 4), (4, 21, 2), (4, 27, 2), (4, 35, 3), (4, 36, 2), (5, 1, 7), (5, 13, 5), (5, 15, 4), (5, 21, 3), (5, 27, 6), (5, 28, 2), (5, 30, 5), (6, 3, 2), (6, 8, 2), (6, 11, 2), (6, 13, 3), (6, 17, 2), (6, 20, 6), (6, 25, 6), (6, 31, 3), (6, 32, 10), (7, 37, 6), (8, 4, 3), (8, 10, 3), (8, 15, 2), (8, 17, 3), (8, 20, 3), (9, 28, 6), (9, 36, 3), (10, 2, 3), (10, 7, 4), (10, 11, 5), (10, 12, 3), (10, 36, 2), (10, 40, 3), (11, 4, 4), (11, 5, 4), (11, 18, 2), (11, 23, 9), (11, 24, 7), (11, 33, 4), (12, 5, 8), (12, 21, 8), (12, 36, 4), (13, 23, 3), (13, 26, 5), (13, 33, 3), (14, 0, 3), (14, 31, 2), (14, 34, 2), (15, 15, 7), (15, 18, 6), (15, 29, 2), (15, 30, 3), (15, 34, 3), (15, 36, 4), (15, 39, 4), (16, 4, 4), (16, 6, 4), (16, 8, 5), (16, 16, 4), (16, 22, 4), (16, 24, 4), (16, 37, 3), (16, 38, 2), (17, 0, 3), (17, 2, 2), (17, 3, 4), (17, 20, 7), (17, 25, 3), (17, 30, 2), (18, 2, 8), (18, 6, 2), (18, 9, 2), (18, 12, 3), (18, 27, 6), (19, 5, 7), (19, 12, 6), (19, 22, 2), (19, 30, 3), (19, 31, 2), (20, 19, 6), (20, 34, 3), (20, 36, 4), (20, 37, 4), (21, 1, 3), (21, 17, 4), (21, 24, 3), (21, 31, 3), (21, 33, 5), (21, 35, 3), (22, 13, 3), (22, 15, 2), (22, 23, 2), (22, 29, 4), (22, 30, 3), (22, 34, 6), (23, 0, 4), (23, 1, 2), (23, 7, 2), (23, 21, 2), (23, 25, 3), (23, 28, 5), (23, 32, 4), (23, 34, 3), (23, 37, 5), (24, 1, 2), (24, 12, 3), (24, 13, 4), (24, 34, 2), (25, 8, 2), (25, 9, 8), (25, 12, 2), (25, 14, 3), (25, 21, 3), (25, 26, 2), (25, 30, 2), (25, 33, 7), (26, 9, 2), (26, 12, 3), (27, 3, 2), (27, 34, 3), (27, 36, 3), (27, 37, 2), (28, 7, 3), (28, 11, 2), (28, 17, 7), (28, 19, 6), (28, 23, 2), (28, 30, 5), (28, 36, 2), (29, 15, 3), (29, 18, 4), (29, 23, 2), (29, 28, 3), (29, 35, 2), (30, 4, 4), (30, 8, 2), (30, 10, 2), (30, 19, 2), (30, 29, 3), (30, 38, 2), (31, 4, 2), (31, 17, 3), (31, 28, 4), (31, 34, 4), (32, 8, 2), (32, 10, 5), (32, 15, 3), (32, 21, 5), (32, 33, 5), (33, 4, 3), (33, 7, 2), (33, 16, 2), (33, 19, 8), (33, 27, 2), (33, 31, 3), (34, 7, 2), (34, 20, 2), (35, 14, 3), (35, 25, 3), (35, 26, 3), (35, 28, 2), (35, 35, 5), (35, 37, 3), (36, 16, 2), (36, 32, 2), (36, 37, 3), (37, 1, 3), (37, 10, 3), (37, 22, 3), (37, 26, 4), (37, 28, 4), (37, 29, 3), (37, 36, 4), (38, 20, 4), (38, 26, 4), (38, 32, 2), (39, 1, 4), (39, 7, 4), (39, 12, 4), (39, 17, 3), (39, 20, 3), (39, 23, 3), (39, 30, 2), (39, 39, 14), (40, 17, 3), (40, 23, 5), (40, 29, 4)]


def main(size,white_circles,black_circles):#呃，这一套全是珍珠的，我只是把珍珠的代码复制过来然后把珍珠的独特部分全删了
    #初始化grid，数据结构同数回
    size+=1#原来的size是珍珠的坐标，而现在相当于向右下延申，只需要加1
    grid=Grid([[0]*(size) for _ in range(size)])
    #求解就是大一统的过程
    p=1
    for y, x in product(range(1,size-1), range(1,size-1)):
        grid[y][x]=p
        p+=1


    white_dict = {(r, c): num for r, c, num in white_circles}
    black_dict = {(r, c): num for r, c, num in black_circles}
    #信号旗独特逻辑，初始化“上下左右可延申数量表”；格式为[[[上的可能数字],[下的可能数字],[左的可能数字],[右的可能数字]],……]，和circles一一对应
    white_excel=[]
    black_excel=[]
    for i in white_circles:
        white_excel.append([[j for j in range(i[2])] for _ in range(4)])
    for i in black_circles:
        black_excel.append([[j for j in range(i[2])] for _ in range(4)])
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
            grid[y][x]=-1
            print(grid[21][32],grid[22][32],grid[21][32]==xorint(grid[22][32]))
            show_shingoki(size, white_circles,black_circles, grid)
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
    effect=1
    test=0
    #一次性结构

    #处理黑白子的边界情况，保证后面不出界（注意这里就已经不考虑边缘一圈0）
    for r,i in zip(white_circles+black_circles,white_excel+black_excel):
        i[0]=[a for a in i[0] if r[0]-a>=0]#上
        i[1]=[a for a in i[1] if r[0]+a<size-1]#下
        i[2]=[a for a in i[2] if r[1]-a>=0]#左
        i[3]=[a for a in i[3] if r[1]+a<size-1]#右

    #处理黑白子延伸出去碰到黑白子的情况，这里就复杂了
    for r,i in zip(white_circles,white_excel):
        y,x,number=r
        for d,(dy,dx) in enumerate([(-1,0),(1,0),(0,-1),(0,1)]):
            for p in i[d]:
                if p==0:
                    continue
                if (y+dy*p,x+dx*p) in white_dict:
                    if white_dict[(y+dy*p,x+dx*p)]==number:#同样数字的白
                        i[d]=[a for a in i[d] if a!=p]
                        continue
                    else:#不同数字的白，道不同不相为谋
                        i[d]=[a for a in i[d] if a<p]
                        break
                if (y+dy*p,x+dx*p) in black_dict:
                    if black_dict[(y+dy*p,x+dx*p)]>number:#还好，吃得下
                        i[d]=[a for a in i[d] if a<=p]#不能穿过黑色
                        break
                    else:
                        i[d]=[a for a in i[d] if a<p]#不能碰到黑色
                        break


    for r,i in zip(black_circles,black_excel):
        y,x,number=r
        for d,(dy,dx) in enumerate([(-1,0),(1,0),(0,-1),(0,1)]):
            for p in i[d]:
                if p==0:
                    continue
                if (y+dy*p,x+dx*p) in white_dict:
                    if p<white_dict[(y+dy*p,x+dx*p)]<number:#这个黑吃得下且距离够
                        i[d]=[a for a in i[d] if (a<p or a==white_dict[(y+dy*p,x+dx*p)])]
                        continue
                    else:#总之这个黑不能吃
                        i[d]=[a for a in i[d] if a<p]
                        break
                if (y+dy*p,x+dx*p) in black_dict:
                    if p<black_dict[(y+dy*p,x+dx*p)]:#那个黑色吃得下
                        i[d]=[a for a in i[d] if a<=p]#不能穿过黑色
                        break
                    else:
                        i[d]=[a for a in i[d] if a<p]#不能碰到黑色
                        break

    #白子的对角仍然不同
    for y,x,_ in white_circles:
        check=find_diy(y,x,('tian',0))#不会出界
        #对角不同，这已经包含水平垂直了
        effect+=modify(*check[3],xorint(grid[check[0]]))
        effect+=modify(*check[2],xorint(grid[check[1]]))

    #难度其实最高，但越后面越能复用
    while effect>0:
        effect=0
        #独特逻辑：黑·白（信号旗版）：分别探上下左右能走的格数集合，然后进行相加
        for r,i in zip(white_circles,white_excel):
            if 0:
                break
            y,x,number=r
            #如果开始前i就都确定好了，那就没必要下去了
            if_end=[len(a)==1 for a in i]
            if all(if_end):
                continue
            #探一下有没有颜色错误
            for d,(dy,dx,dire) in enumerate([(-1,0,'up'),(1,0,'down'),(0,-1,'left'),(0,1,'right')]):
                yibian=set()
                lingyibian=set()
                for p in range(1,max(i[d])+1):
                    asdf,zxcv=grid[find_diy(y,x,(dire,p))[0]],grid[find_diy(y,x,(dire,p))[1]]
                    if xorint(asdf) in yibian or asdf in lingyibian:#冲突了
                        i[d]=[a for a in i[d] if a<p]
                        break
                    else:
                        yibian.add(asdf)
                    if xorint(zxcv) in lingyibian or zxcv in yibian:#冲突了
                        i[d]=[a for a in i[d] if a<p]
                        break
                    else:
                        lingyibian.add(zxcv)
                    if asdf==xorint(zxcv) and len(yibian)==1 and len(lingyibian)==1:#外力让它俩隔离了，那只能顺从了
                        i[d]=[a for a in i[d] if a>=p or a==0]
            #探好了，现在进入核心！
            #水平和竖直分别互相匹配
            i[0]=[a for a in i[0] if number-a in i[1] or a==0]
            i[1]=[a for a in i[1] if number-a in i[0] or a==0]
            i[2]=[a for a in i[2] if number-a in i[3] or a==0]
            i[3]=[a for a in i[3] if number-a in i[2] or a==0]
            #看看有没有决定是水平还是竖直
            if i[0]==[0] or i[1]==[0]:#竖直失败！只能水平！
                if 0 in i[2]:
                    i[2].remove(0)
                if 0 in i[3]:
                    i[3].remove(0)
                #开始染色！左右分别染最小颜色
                yibiandeyanse,lingyibiandeyanse=grid[find_diy(y,x,('left',0))[0]],grid[find_diy(y,x,('left',0))[1]]
                for p in range(min(i[2])+1):
                    effect+=modify(*find_diy(y,x,('left',p))[0],yibiandeyanse)
                    effect+=modify(*find_diy(y,x,('left',p))[1],lingyibiandeyanse)
                if len(i[2])==1:#已经确定了啊
                    effect+=modify(*find_diy(y,x,('left',p+1))[0],grid[find_diy(y,x,('left',p+1))[1]])#这里直接借了刚刚for循环的p，我承认这很耦合，但很精妙啊
                for p in range(min(i[3])+1):
                    effect+=modify(*find_diy(y,x,('right',p))[0],yibiandeyanse)
                    effect+=modify(*find_diy(y,x,('right',p))[1],lingyibiandeyanse)
                if len(i[3])==1:#已经确定了啊
                    effect+=modify(*find_diy(y,x,('right',p+1))[0],grid[find_diy(y,x,('right',p+1))[1]])
            if i[2]==[0] or i[3]==[0]:#水平失败！只能竖直！
                if 0 in i[0]:
                    i[0].remove(0)
                if 0 in i[1]:
                    i[1].remove(0)
                #开始染色！左右分别染最小颜色
                yibiandeyanse,lingyibiandeyanse=grid[find_diy(y,x,('up',0))[0]],grid[find_diy(y,x,('down',0))[1]]
                for p in range(min(i[0])+1):
                    effect+=modify(*find_diy(y,x,('up',p))[0],yibiandeyanse)
                    effect+=modify(*find_diy(y,x,('up',p))[1],lingyibiandeyanse)
                if len(i[0])==1:#已经确定了啊
                    effect+=modify(*find_diy(y,x,('up',p+1))[0],grid[find_diy(y,x,('up',p+1))[1]])
                for p in range(min(i[1])+1):
                    effect+=modify(*find_diy(y,x,('down',p))[0],yibiandeyanse)
                    effect+=modify(*find_diy(y,x,('down',p))[1],lingyibiandeyanse)
                if len(i[1])==1:#已经确定了啊
                    effect+=modify(*find_diy(y,x,('down',p+1))[0],grid[find_diy(y,x,('down',p+1))[1]])


        for r,i in zip(black_circles,black_excel):
            if 0:
                break
            y,x,number=r
            #如果开始前i就都确定好了，那就没必要下去了
            if_end=[len(a)==1 for a in i]
            if all(if_end):
                continue

            if r==(21,33,5) and test==2:
                    print('czhdsb1',r,i)
                    show_shingoki(size, white_circles, black_circles, grid)

            #探一下有没有颜色错误
            for d,(dy,dx,dire) in enumerate([(-1,0,'up'),(1,0,'down'),(0,-1,'left'),(0,1,'right')]):
                yibian=set()
                lingyibian=set()
                for p in range(1,max(i[d])+1):
                    if p==0:
                        continue
                    asdf,zxcv=grid[find_diy(y,x,(dire,p))[0]],grid[find_diy(y,x,(dire,p))[1]]
                    if xorint(asdf) in yibian or asdf in lingyibian:#冲突了
                        i[d]=[a for a in i[d] if a<p]
                        break
                    else:
                        yibian.add(asdf)
                    if xorint(zxcv) in lingyibian or zxcv in yibian:#冲突了
                        i[d]=[a for a in i[d] if a<p]
                        break
                    else:
                        lingyibian.add(zxcv)
                    if asdf==xorint(zxcv) and len(yibian)==1 and len(lingyibian)==1 and 1:#外力让它俩隔离了，那只能顺从了
                        i[d]=[a for a in i[d] if a>=p or a==0]
                if p==max(i[d]):
                    asdf,zxcv=grid[find_diy(y,x,(dire,p))[0]],grid[find_diy(y,x,(dire,p))[1]]
                    asdf1,zxcv1=grid[find_diy(y,x,(dire,p+1))[0]],grid[find_diy(y,x,(dire,p+1))[1]]
                    if asdf==asdf1 and zxcv==zxcv1:#多一个还是行，那最大就不行了
                        i[d].remove(p)
            if r==(21,33,5) and test==2:
                    print('czhdsb2',r,i)
                    show_shingoki(size, white_circles, black_circles, grid)


            #探好了，现在进入核心！
            #水平和竖直之间匹配
            shuzhizong=set(i[0]+i[1])
            shuipingzong=set(i[2]+i[3])
            i[0]=[a for a in i[0] if number-a in shuipingzong or a==0]
            i[1]=[a for a in i[1] if number-a in shuipingzong or a==0]
            i[2]=[a for a in i[2] if number-a in shuzhizong or a==0]
            i[3]=[a for a in i[3] if number-a in shuzhizong or a==0]
            #看看有没有决定水平和竖直的方向
            shuiping,shuzhi=None,None
            if i[0]==[0]:#上不行了
                shuzhi='down'
                if 0 in i[1]:
                    i[1].remove(0)
                shuzhikeneng=i[1]
                effect+=modify(*find_diy(y,x,('up',1))[0],grid[find_diy(y,x,('up',1))[1]])#那么上面两格肯定要相同啊
                effect+=modify(*find_diy(y,x,('down',1))[0],xorint(grid[find_diy(y,x,('down',1))[1]]))#那么下面两格肯定要不同啊
            elif i[1]==[0]:
                shuzhi='up'
                if 0 in i[0]:
                    i[0].remove(0)
                shuzhikeneng=i[0]
                effect+=modify(*find_diy(y,x,('down',1))[0],grid[find_diy(y,x,('down',1))[1]])
                effect+=modify(*find_diy(y,x,('up',1))[0],xorint(grid[find_diy(y,x,('up',1))[1]]))
            if i[2]==[0]:
                shuiping='right'
                if 0 in i[3]:
                    i[3].remove(0)
                shuipingkeneng=i[3]
                effect+=modify(*find_diy(y,x,('left',1))[0],grid[find_diy(y,x,('left',1))[1]])
                effect+=modify(*find_diy(y,x,('right',1))[0],xorint(grid[find_diy(y,x,('right',1))[1]]))
            elif i[3]==[0]:
                shuiping='left'
                if 0 in i[2]:
                    i[2].remove(0)
                shuipingkeneng=i[2]
                effect+=modify(*find_diy(y,x,('right',1))[0],grid[find_diy(y,x,('right',1))[1]])
                effect+=modify(*find_diy(y,x,('left',1))[0],xorint(grid[find_diy(y,x,('left',1))[1]]))


            if r==(21,33,5) and test==2:
                    print('czhdsb3',r,i)
                    show_shingoki(size, white_circles, black_circles, grid)


            if shuzhi and 1:#依旧采用最小染色！
                yibiandeyanse,lingyibiandeyanse=grid[find_diy(y,x,(shuzhi,1))[0]],grid[find_diy(y,x,(shuzhi,1))[1]]
                for p in range(1,min(shuzhikeneng)+1):
                    effect+=modify(*find_diy(y,x,(shuzhi,p))[0],yibiandeyanse)
                    effect+=modify(*find_diy(y,x,(shuzhi,p))[1],lingyibiandeyanse)
                if len(shuzhikeneng)==1 and 1:#已经确定了啊
                    effect+=modify(*find_diy(y,x,(shuzhi,p+1))[0],grid[find_diy(y,x,(shuzhi,p+1))[1]])
            if shuiping and 1:
                yibiandeyanse,lingyibiandeyanse=grid[find_diy(y,x,(shuiping,1))[0]],grid[find_diy(y,x,(shuiping,1))[1]]
                for p in range(1,min(shuipingkeneng)+1):
                    effect+=modify(*find_diy(y,x,(shuiping,p))[0],yibiandeyanse)
                    effect+=modify(*find_diy(y,x,(shuiping,p))[1],lingyibiandeyanse)
                if len(shuipingkeneng)==1 and 1:#已经确定了啊
                    effect+=modify(*find_diy(y,x,(shuiping,p+1))[0],grid[find_diy(y,x,(shuiping,p+1))[1]])
                    1

        #小结构
        #最强的小结构，依旧禁止国际棋盘
        for y, x in product(range(1,size-1), range(1,size-1)):
            tian=((y,x),(y+1,x),(y+1,x+1),(y,x+1))#本，下，右下，右
            tianlist=[grid[temp] for temp in tian]
            tianintlist=set(map(lambda x:int(x),tianlist))
            if len(tianintlist)==1:#统一了，没你事了
                continue
            if tianlist[0]==tianlist[2]:#根据tian硬编码了，但记住这是左上右下对角相等
                if xorint(tianlist[1])==tianlist[0]:#危险，tianlist[3]必须挽回
                    effect+=modify(*tian[3],tianlist[0])
                if xorint(tianlist[3])==tianlist[0]:#同样，tianlist[1]必须挽回
                    effect+=modify(*tian[1],tianlist[0])
                
            if tianlist[1]==tianlist[3]:#根据tian硬编码了，但记住这是右上左下对角相等
                if xorint(tianlist[0])==tianlist[1]:#危险，tianlist[2]必须挽回
                    effect+=modify(*tian[2],tianlist[1])
                if xorint(tianlist[2])==tianlist[1]:#同样，tianlist[0]必须挽回
                    effect+=modify(*tian[0],tianlist[1])
            #特殊的来了，上俩相异下俩相异
            if tianlist[0]==xorint(tianlist[1]) and tianlist[2]==xorint(tianlist[3]):
                effect+=modify(*tian[0],tianlist[3])
            if tianlist[0]==xorint(tianlist[3]) and tianlist[2]==xorint(tianlist[1]):
                effect+=modify(*tian[0],tianlist[1])


        #连通性部分
        liantong4=[]
        #1、现有格子加入liantong系列
        visited=set()
        for y, x in product(range(size), range(size)):
            if 0:
                break
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
        if effect==0 and 1:
            #生成所有除0以外格子集合
            gezi_except_0=set()
            for y, x in product(range(size), range(size)):
                if grid[y][x]!=0:
                    gezi_except_0.add((y,x))
            for i in gezi_except_0:#遍历每一个0.5以外元素，i是禁忌元素
                if grid[i[0]][i[1]]==0.5:
                    continue
                zu=grid[i[0]][i[1]]
                # 剪枝 1：有效邻居太少的不可能是割点
                ne_valid = [nb for nb in find_neig4(*i) if nb in gezi_except_0]
                if len(ne_valid) <= 1:
                    continue
                # 找到起点 (避开被抠掉的 i)
                start = ne_valid[0]

                # 剪枝 2：快速测试它的几个邻居之间能否绕开 i 互相连通
                stack = [start]
                for y1, x1 in product(range(size), range(size)):#修复了一个陈年bug……
                    if grid[y1][x1]==zu:
                        stack.append((y1,x1))
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
    if 1:
        size-=2
        grid=[grid[i][1:size+1] for i in range(1,size+1)]
    return grid


grid=main(size,white_circles,black_circles)
#理论上最后应该画线，但懒得画了
show_shingoki(size, white_circles, black_circles, grid)