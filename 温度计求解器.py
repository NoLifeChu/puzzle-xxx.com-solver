import tkinter as tk
import math
from playwright.sync_api import sync_playwright

def show_thermometers(size, row_tasks, col_tasks, thermometers, minlen, maxlen):
    """
    温度计高保真物理流体可视化窗口 (长宽归一版):
    - size: 正方形棋盘边长 N
    - row_tasks, col_tasks: 行列目标线索
    - thermometers: 每根温度计完整有序路径
    - minlen, maxlen: 水银下界与上界
    """
    root = tk.Tk()
    root.title(f"Thermometers Bounds Visualizer ({size}x{size})")

    # 根据尺寸自适应格子大小 (控制在 750px 左右)
    cell_size = max(18, min(42, 750 // size))

    # 边距参数
    m_left = max(35, int(cell_size * 1.5))    # 左侧行目标
    m_top = max(30, int(cell_size * 1.3))     # 顶部列目标
    m_right = max(55, int(cell_size * 2.2))   # 右侧行状态对账
    m_bottom = max(35, int(cell_size * 1.5))  # 底部列状态对账

    canvas_w = m_left + size * cell_size + m_right
    canvas_h = m_top + size * cell_size + m_bottom

    canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="#FFFFFF")
    canvas.pack(padx=10, pady=10)

    # 辅助函数：将网格坐标转换为中心像素坐标
    def get_center(r, c):
        return m_left + c * cell_size + cell_size / 2, m_top + r * cell_size + cell_size / 2

    # 1. 绘制底层背景网格
    for r in range(size):
        for c in range(size):
            x1 = m_left + c * cell_size
            y1 = m_top + r * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            canvas.create_rectangle(x1, y1, x2, y2, fill="#FAFAFC", outline="#E4E4EB", width=1)

    # 2. 图层一：绘制完整贯通的玻璃外壳导管 (从水银泡一直画到真正的尾部！)
    COLOR_OUTLINE = "#8C959F"   # 导管轮廓深灰
    COLOR_GLASS   = "#FFFFFF"   # 玻璃管内腔透明白

    pipe_outer_w = cell_size * 0.54
    pipe_inner_w = cell_size * 0.44
    bulb_r_outer = cell_size * 0.40
    bulb_r_inner = cell_size * 0.35

    for path in thermometers:
        # A1. 轮廓底色
        for i in range(len(path)):
            cx, cy = get_center(path[i][0], path[i][1])
            if i == 0:
                canvas.create_oval(cx - bulb_r_outer, cy - bulb_r_outer, cx + bulb_r_outer, cy + bulb_r_outer, 
                                   fill=COLOR_OUTLINE, outline="")
            if i > 0:
                px, py = get_center(path[i - 1][0], path[i - 1][1])
                canvas.create_line(px, py, cx, cy, fill=COLOR_OUTLINE, width=pipe_outer_w, capstyle=tk.ROUND)
                canvas.create_oval(cx - pipe_outer_w/2, cy - pipe_outer_w/2, cx + pipe_outer_w/2, cy + pipe_outer_w/2, 
                                   fill=COLOR_OUTLINE, outline="")

        # A2. 玻璃管内腔亮白底
        for i in range(len(path)):
            cx, cy = get_center(path[i][0], path[i][1])
            if i == 0:
                canvas.create_oval(cx - bulb_r_inner, cy - bulb_r_inner, cx + bulb_r_inner, cy + bulb_r_inner, 
                                   fill=COLOR_GLASS, outline="")
            if i > 0:
                px, py = get_center(path[i - 1][0], path[i - 1][1])
                canvas.create_line(px, py, cx, cy, fill=COLOR_GLASS, width=pipe_inner_w, capstyle=tk.ROUND)
                canvas.create_oval(cx - pipe_inner_w/2, cy - pipe_inner_w/2, cx + pipe_inner_w/2, cy + pipe_inner_w/2, 
                                   fill=COLOR_GLASS, outline="")

    # 3. 图层二：注入确定灌满的红色水银流体 (仅灌入 0 到 minlen[idx]-1)
    COLOR_MERCURY = "#D32F2F"   # 纯正水银红
    mercury_pipe_w = cell_size * 0.42
    mercury_bulb_r = cell_size * 0.33

    for idx, path in enumerate(thermometers):
        min_l = minlen[idx]
        if min_l <= 0:
            continue

        for i in range(min(min_l, len(path))):
            cx, cy = get_center(path[i][0], path[i][1])
            if i == 0:
                canvas.create_oval(cx - mercury_bulb_r, cy - mercury_bulb_r, cx + mercury_bulb_r, cy + mercury_bulb_r, 
                                   fill=COLOR_MERCURY, outline="")
            if i > 0:
                px, py = get_center(path[i - 1][0], path[i - 1][1])
                canvas.create_line(px, py, cx, cy, fill=COLOR_MERCURY, width=mercury_pipe_w, capstyle=tk.ROUND)
                canvas.create_oval(cx - mercury_pipe_w/2, cy - mercury_pipe_w/2, cx + mercury_pipe_w/2, cy + mercury_pipe_w/2, 
                                   fill=COLOR_MERCURY, outline="")

    # 4. 图层三：在确定不能放水银的空管上，覆盖印上准星叉 ❌ (j >= maxlen[idx])
    d = cell_size * 0.17
    for idx, path in enumerate(thermometers):
        max_l = maxlen[idx]
        for j in range(max_l, len(path)):
            cx, cy = get_center(path[j][0], path[j][1])
            canvas.create_line(cx - d, cy - d, cx + d, cy + d, fill="#4A5568", width=2.5)
            canvas.create_line(cx - d, cy + d, cx + d, cy - d, fill="#4A5568", width=2.5)

    # 5. 绘制四周线索与实时对账仪表盘
    font_task = ("Arial", max(8, int(cell_size * 0.42)), "bold")
    font_check = ("Consolas", max(7, int(cell_size * 0.42)), "bold")

    # 统计全盘各格状态
    cell_state = [[-1] * size for _ in range(size)]
    for idx, path in enumerate(thermometers):
        min_l, max_l = minlen[idx], maxlen[idx]
        for step, (r, c) in enumerate(path):
            if step < min_l: cell_state[r][c] = 1
            elif step >= max_l: cell_state[r][c] = 2
            else: cell_state[r][c] = 0

    # 顶部与底部：列线索与核算
    for c in range(size):
        cx = m_left + c * cell_size + cell_size / 2
        target = col_tasks[c]
        confirmed_red = sum(1 for r in range(size) if cell_state[r][c] == 1)
        can_be_red    = sum(1 for r in range(size) if cell_state[r][c] in (0, 1))

        canvas.create_text(cx, m_top / 2, text=str(target), fill="#1A1A1E", font=font_task)

        by = m_top + size * cell_size + m_bottom / 2
        if confirmed_red == target == can_be_red:
            canvas.create_text(cx, by, text="✔", fill="#2E7D32", font=font_check)
        else:
            canvas.create_text(cx, by, text=f"{confirmed_red}~{can_be_red}", fill="#4B5563", font=font_check)

    # 左侧与右侧：行线索与核算
    for r in range(size):
        cy = m_top + r * cell_size + cell_size / 2
        target = row_tasks[r]
        confirmed_red = sum(1 for c in range(size) if cell_state[r][c] == 1)
        can_be_red    = sum(1 for c in range(size) if cell_state[r][c] in (0, 1))

        canvas.create_text(m_left / 2, cy, text=str(target), fill="#1A1A1E", font=font_task)

        rx = m_left + size * cell_size + m_right / 2
        if confirmed_red == target == can_be_red:
            canvas.create_text(rx, cy, text="✔", fill="#2E7D32", font=font_check)
        else:
            canvas.create_text(rx, cy, text=f"{confirmed_red}~{can_be_red}", fill="#4B5563", font=font_check)

    # 棋盘外框
    canvas.create_rectangle(m_left, m_top, m_left + size * cell_size, m_top + size * cell_size, outline="#24292F", width=2)

    root.mainloop()


def fetch_thermometers(url="https://www.puzzle-thermometers.com/"):
    """
    后台静默抓取温度计题目页面，返回 (size, row_tasks, col_tasks, thermometers)
    - size: 正方形棋盘边长 N
    - row_tasks: 行目标数字列表
    - col_tasks: 列目标数字列表
    - thermometers: 每根温度计从水银泡到封口的有序元组列表
    """
    print(f"正在后台启动无头浏览器抓取温度计题目: {url} ...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        page.wait_for_selector('div[tabindex="-1"].cell.selectable')

        data = page.evaluate("""() => {
            let cells = Array.from(document.querySelectorAll('div[tabindex="-1"]')).filter(c => 
                c.classList.contains('cell') && c.classList.contains('selectable')
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
            let size = sortedRowTops.length;

            let gridElements = [];
            for (let topKey of sortedRowTops) {
                let rowCells = rowsMap.get(topKey);
                rowCells.sort((a, b) => a.offsetLeft - b.offsetLeft);
                gridElements.push(rowCells);
            }

            const UP = [-1, 0], RIGHT = [0, 1], DOWN = [1, 0], LEFT = [0, -1];
            function getPorts(el) {
                let r = 0;
                if (el.classList.contains('r1')) r = 1;
                else if (el.classList.contains('r2')) r = 2;
                else if (el.classList.contains('r3')) r = 3;

                if (el.classList.contains('start') || el.classList.contains('end')) {
                    if (r === 0) return [UP];
                    if (r === 1) return [RIGHT];
                    if (r === 2) return [DOWN];
                    if (r === 3) return [LEFT];
                } else if (el.classList.contains('straight')) {
                    if (r === 0 || r === 2) return [UP, DOWN];
                    if (r === 1 || r === 3) return [LEFT, RIGHT];
                } else if (el.classList.contains('curve')) {
                    if (r === 0) return [UP, RIGHT];
                    if (r === 1) return [RIGHT, DOWN];
                    if (r === 2) return [DOWN, LEFT];
                    if (r === 3) return [LEFT, UP];
                }
                return [];
            }

            let thermometers = [];
            let visited = Array.from({length: size}, () => Array(size).fill(false));

            for (let r = 0; r < size; r++) {
                for (let c = 0; c < size; c++) {
                    let el = gridElements[r][c];
                    if (el.classList.contains('start') && !visited[r][c]) {
                        let path = [[r, c]];
                        visited[r][c] = true;

                        let curr_r = r, curr_c = c;
                        let ports = getPorts(el);
                        if (ports.length === 0) continue;

                        let prev_r = curr_r, prev_c = curr_c;
                        curr_r += ports[0][0];
                        curr_c += ports[0][1];

                        while (true) {
                            if (curr_r < 0 || curr_r >= size || curr_c < 0 || curr_c >= size) break;
                            let nextEl = gridElements[curr_r][curr_c];
                            if (!nextEl) break;

                            path.push([curr_r, curr_c]);
                            visited[curr_r][curr_c] = true;

                            if (nextEl.classList.contains('end')) break;

                            let nextPorts = getPorts(nextEl);
                            let forwardPort = nextPorts.find(p => (curr_r + p[0] !== prev_r) || (curr_c + p[1] !== prev_c));
                            if (!forwardPort) break;

                            prev_r = curr_r;
                            prev_c = curr_c;
                            curr_r += forwardPort[0];
                            curr_c += forwardPort[1];
                        }
                        thermometers.push(path);
                    }
                }
            }

            let rowTaskEls = Array.from(document.querySelectorAll('.cell.task.h, .task.h'));
            rowTaskEls.sort((a, b) => a.offsetTop - b.offsetTop);
            let row_tasks = rowTaskEls.map(el => parseInt(el.innerText.trim())).filter(n => !isNaN(n)).slice(0, size);

            let colTaskEls = Array.from(document.querySelectorAll('.cell.task.v, .task.v'));
            colTaskEls.sort((a, b) => a.offsetLeft - b.offsetLeft);
            let col_tasks = colTaskEls.map(el => parseInt(el.innerText.trim())).filter(n => !isNaN(n)).slice(0, size);

            return {
                size: size,
                row_tasks: row_tasks,
                col_tasks: col_tasks,
                thermometers: thermometers
            };
        }""")

        browser.close()
        print(f"✔ 温度计抓取成功！正方形尺寸: {data['size']}x{data['size']}, 共 {len(data['thermometers'])} 根导管")
        return data["size"], data["row_tasks"], data["col_tasks"], data["thermometers"]


def entropy():
    a=0
    for i in range(len(thermometers)):
        a += math.log2(maxlen[i]-minlen[i]+1)
    return a

#size,row_tasks,col_tasks,thermometers=fetch_thermometers(url="https://www.puzzle-thermometers.com/")

#一个弯曲的例子
size = 20
row_tasks = [11,13,6,16,18,12,7,6,6,7,9,10,7,7,8,11,11,7,12,15]
col_tasks = [5,11,6,9,13,8,8,6,16,16,8,18,15,8,13,5,3,14,6,11]
thermometers = (((0,2),(0,1),(0,0),(1,0)),((0,3),(0,4),(0,5),(0,6),(0,7),(0,8),(0,9),(0,10),(0,11),(0,12),(0,13),(0,14),(0,15),(0,16),(0,17),(0,18),(0,19),(1,19),(2,19)),((2,0),(3,0),(4,0),(5,0),(6,0),(7,0),(8,0),(9,0),(10,0),(11,0),(12,0),(13,0),(14,0),(15,0),(16,0),(17,0),(17,1)),((2,7),(1,7),(1,8),(2,8),(3,8),(4,8),(5,8),(6,8),(7,8),(8,8),(9,8),(10,8),(11,8),(12,8),(13,8),(14,8),(15,8),(16,8),(17,8),(17,9)),((2,10),(3,10)),((2,14),(2,13)),((3,6),(2,6),(1,6),(1,5),(1,4),(1,3),(1,2),(1,1),(2,1)),((4,7),(3,7)),((4,10),(5,10)),((4,15),(3,15),(2,15),(2,16)),((5,2),(4,2),(3,2),(2,2),(2,3),(2,4),(2,5)),((5,3),(4,3),(3,3),(3,4),(4,4),(5,4),(6,4),(7,4),(8,4),(9,4),(10,4),(10,3),(9,3),(8,3),(7,3),(6,3),(6,2)),((5,5),(5,6),(4,6),(4,5),(3,5)),((5,13),(6,13),(7,13),(8,13),(9,13),(10,13),(11,13),(12,13)),((5,18),(4,18),(3,18),(2,18),(1,18),(1,17),(1,16),(1,15),(1,14),(1,13),(1,12),(1,11),(1,10),(1,9),(2,9),(3,9),(4,9),(5,9),(6,9),(7,9),(8,9),(9,9),(10,9),(11,9),(12,9),(13,9),(14,9),(15,9),(16,9)),((6,10),(7,10),(8,10)),((6,17),(5,17),(4,17),(4,16),(3,16),(3,17),(2,17)),((7,2),(8,2),(9,2),(10,2),(11,2),(12,2),(13,2),(14,2),(14,3)),((7,17),(8,17),(9,17),(10,17),(11,17),(12,17),(13,17),(14,17),(15,17),(16,17),(16,16)),((8,15),(9,15),(10,15),(11,15)),((9,6),(8,6),(7,6),(6,6),(6,5),(7,5)),((9,10),(10,10),(11,10),(12,10),(13,10)),((9,12),(8,12),(7,12)),((9,18),(8,18),(7,18),(6,18)),((10,12),(11,12),(12,12),(13,12),(14,12),(15,12),(16,12),(17,12),(18,12),(18,13),(18,14),(18,15),(18,16)),((11,1),(10,1),(9,1),(8,1),(7,1),(6,1),(5,1),(4,1),(3,1)),((11,3),(11,4),(11,5),(11,6),(10,6),(10,5),(9,5),(8,5)),((11,18),(10,18)),((12,1),(13,1),(14,1)),((12,3),(12,4),(12,5),(12,6),(13,6),(13,5)),((13,3),(13,4),(14,4)),((13,13),(14,13),(15,13)),((14,10),(15,10),(16,10),(17,10),(18,10),(18,11),(17,11),(16,11),(15,11),(14,11),(13,11),(12,11),(11,11),(10,11),(9,11),(8,11),(7,11),(6,11),(6,12),(5,12),(5,11),(4,11),(4,12),(4,13),(4,14),(3,14),(3,13),(3,12),(2,12),(2,11),(3,11)),((15,3),(15,2)),((15,4),(15,5),(15,6),(14,6),(14,5)),((16,5),(16,4),(16,3),(16,2),(16,1),(15,1)),((16,6),(17,6),(17,5),(17,4),(17,3),(17,2)),((16,13),(17,13),(17,14),(16,14),(15,14),(14,14),(13,14),(12,14),(11,14),(10,14),(9,14),(8,14),(7,14),(7,15),(6,15),(6,14),(5,14),(5,15),(5,16),(6,16),(7,16),(8,16),(9,16),(10,16),(11,16),(12,16),(13,16),(14,16),(15,16)),((17,15),(16,15),(15,15),(14,15),(13,15),(12,15)),((18,0),(18,1),(18,2),(18,3)),((18,6),(19,6),(19,7),(18,7),(17,7),(16,7),(15,7),(14,7),(13,7),(12,7),(11,7),(10,7),(9,7),(8,7),(7,7),(6,7),(5,7)),((18,9),(18,8)),((19,0),(19,1),(19,2),(19,3),(19,4),(19,5),(18,5),(18,4)),((19,9),(19,8)),((19,10),(19,11),(19,12),(19,13),(19,14),(19,15)),((19,16),(19,17),(18,17),(17,17),(17,16)),((19,18),(18,18),(17,18),(16,18),(15,18),(14,18),(13,18),(12,18)),((19,19),(18,19),(17,19),(16,19),(15,19),(14,19),(13,19),(12,19),(11,19),(10,19),(9,19),(8,19),(7,19),(6,19),(5,19),(4,19),(3,19)))

#一个直的例子
size = 25
row_tasks = [13,1,15,12,12,12,7,9,13,9,8,18,18,20,12,21,12,16,14,19,7,5,11,14,14]
col_tasks = [10,1,2,3,6,6,7,7,22,19,14,22,17,17,18,16,21,15,16,14,15,13,19,5,7]
thermometers = (((0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7),(0,8)),((0,9),(0,10),(0,11)),((0,13),(0,12)),((0,18),(0,17),(0,16),(0,15),(0,14)),((0,23),(0,22),(0,21),(0,20),(0,19)),((0,24),(1,24),(2,24),(3,24),(4,24)),((1,0),(1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(1,7),(1,8),(1,9),(1,10),(1,11),(1,12),(1,13),(1,14),(1,15),(1,16),(1,17),(1,18),(1,19),(1,20),(1,21),(1,22),(1,23)),((2,0),(3,0),(4,0)),((2,2),(3,2)),((2,3),(2,4),(2,5),(2,6),(2,7)),((2,8),(3,8),(4,8),(5,8),(6,8)),((2,9),(2,10),(2,11),(2,12)),((2,13),(3,13)),((2,23),(2,22),(2,21),(2,20),(2,19),(2,18),(2,17),(2,16),(2,15),(2,14)),((3,3),(3,4),(3,5),(3,6),(3,7)),((3,10),(3,11),(3,12)),((3,20),(3,19),(3,18),(3,17),(3,16),(3,15),(3,14)),((3,21),(3,22),(3,23)),((4,1),(3,1),(2,1)),((4,2),(5,2),(6,2),(7,2),(8,2),(9,2),(10,2),(11,2)),((4,3),(4,4)),((4,5),(4,6)),((4,7),(5,7)),((4,10),(5,10),(6,10)),((4,18),(4,17),(4,16),(4,15),(4,14),(4,13),(4,12),(4,11)),((4,21),(4,20),(4,19)),((4,23),(4,22)),((5,0),(6,0)),((5,1),(6,1),(7,1),(8,1),(9,1),(10,1)),((5,4),(5,3)),((5,6),(5,5)),((5,11),(5,12),(5,13),(5,14)),((5,15),(6,15)),((5,20),(5,19),(5,18),(5,17),(5,16)),((5,22),(5,23),(5,24)),((6,3),(6,4),(6,5),(6,6),(6,7)),((6,9),(5,9),(4,9),(3,9)),((6,14),(6,13),(6,12),(6,11)),((6,17),(6,16)),((6,19),(6,18)),((6,21),(5,21)),((6,22),(6,23),(6,24)),((7,3),(8,3)),((7,5),(7,4)),((7,9),(7,8),(7,7),(7,6)),((7,17),(7,16),(7,15),(7,14),(7,13),(7,12),(7,11)),((7,19),(8,19)),((7,21),(7,22),(7,23)),((8,4),(8,5),(8,6),(8,7),(8,8),(8,9)),((8,11),(8,12),(8,13),(8,14),(8,15),(8,16)),((8,17),(9,17),(10,17)),((8,20),(7,20),(6,20)),((8,23),(8,22),(8,21)),((8,24),(7,24)),((9,3),(9,4),(9,5),(9,6)),((9,8),(10,8)),((9,11),(9,12),(9,13),(9,14),(9,15)),((9,16),(10,16),(11,16)),((9,18),(8,18),(7,18)),((9,24),(9,23),(9,22),(9,21),(9,20),(9,19)),((10,6),(10,5),(10,4),(10,3)),((10,7),(9,7)),((10,9),(9,9)),((10,10),(9,10),(8,10),(7,10)),((10,11),(10,12)),((10,14),(10,13)),((10,15),(11,15)),((10,19),(10,18)),((10,20),(10,21),(10,22),(10,23),(10,24)),((11,1),(12,1),(13,1),(14,1)),((11,3),(11,4),(11,5),(11,6),(11,7),(11,8),(11,9),(11,10),(11,11),(11,12),(11,13),(11,14)),((11,17),(11,18)),((11,19),(11,20),(11,21),(11,22)),((11,23),(11,24)),((12,5),(12,4),(12,3),(12,2)),((12,6),(12,7),(12,8),(12,9),(12,10),(12,11),(12,12),(12,13),(12,14),(12,15),(12,16),(12,17),(12,18),(12,19),(12,20),(12,21),(12,22),(12,23)),((13,3),(13,2)),((13,4),(13,5),(13,6),(13,7),(13,8)),((13,9),(13,10),(13,11),(13,12),(13,13),(13,14),(13,15),(13,16),(13,17),(13,18),(13,19),(13,20),(13,21),(13,22),(13,23)),((14,2),(14,3)),((14,7),(14,6),(14,5),(14,4)),((14,8),(14,9),(14,10),(14,11),(14,12),(14,13),(14,14),(14,15),(14,16),(14,17),(14,18),(14,19),(14,20)),((14,21),(14,22),(14,23)),((14,24),(13,24),(12,24)),((15,1),(15,2),(15,3)),((15,4),(15,5),(15,6),(15,7),(15,8),(15,9),(15,10),(15,11),(15,12),(15,13),(15,14),(15,15),(15,16),(15,17),(15,18),(15,19),(15,20),(15,21),(15,22)),((15,23),(16,23)),((15,24),(16,24),(17,24),(18,24)),((16,10),(16,9),(16,8),(16,7),(16,6),(16,5),(16,4),(16,3),(16,2),(16,1)),((16,11),(16,12)),((16,18),(16,17),(16,16),(16,15),(16,14),(16,13)),((16,20),(16,19)),((17,1),(18,1)),((17,2),(17,3)),((17,20),(17,19),(17,18),(17,17),(17,16),(17,15),(17,14),(17,13),(17,12),(17,11),(17,10),(17,9),(17,8),(17,7),(17,6),(17,5),(17,4)),((17,23),(18,23),(19,23),(20,23)),((18,0),(17,0),(16,0),(15,0),(14,0),(13,0),(12,0),(11,0),(10,0),(9,0),(8,0),(7,0)),((18,9),(18,8),(18,7),(18,6),(18,5),(18,4),(18,3),(18,2)),((18,10),(19,10)),((18,20),(18,19),(18,18),(18,17),(18,16),(18,15),(18,14),(18,13),(18,12),(18,11)),((18,21),(17,21),(16,21)),((18,22),(17,22),(16,22)),((19,1),(19,0)),((19,2),(19,3),(19,4),(19,5),(19,6),(19,7),(19,8),(19,9)),((19,19),(19,18),(19,17),(19,16),(19,15),(19,14),(19,13),(19,12),(19,11)),((19,20),(19,21),(19,22)),((19,24),(20,24)),((20,22),(20,21),(20,20),(20,19),(20,18),(20,17),(20,16),(20,15),(20,14),(20,13),(20,12),(20,11),(20,10),(20,9),(20,8),(20,7),(20,6),(20,5),(20,4),(20,3),(20,2),(20,1),(20,0)),((21,10),(21,9),(21,8),(21,7),(21,6),(21,5),(21,4),(21,3),(21,2),(21,1),(21,0)),((21,24),(21,23),(21,22),(21,21),(21,20),(21,19),(21,18),(21,17),(21,16),(21,15),(21,14),(21,13),(21,12),(21,11)),((22,0),(22,1)),((22,7),(22,6),(22,5),(22,4),(22,3),(22,2)),((22,9),(22,8)),((22,10),(22,11),(22,12),(22,13),(22,14),(22,15),(22,16),(22,17)),((22,21),(22,20),(22,19),(22,18)),((22,23),(22,24)),((23,0),(23,1),(23,2)),((23,5),(23,4),(23,3)),((23,21),(23,20),(23,19),(23,18),(23,17),(23,16),(23,15),(23,14),(23,13),(23,12),(23,11),(23,10),(23,9),(23,8),(23,7),(23,6)),((23,22),(22,22)),((23,23),(23,24)),((24,2),(24,1),(24,0)),((24,3),(24,4)),((24,6),(24,5)),((24,22),(24,21),(24,20),(24,19),(24,18),(24,17),(24,16),(24,15),(24,14),(24,13),(24,12),(24,11),(24,10),(24,9),(24,8),(24,7)),((24,24),(24,23)))


thermometers_dict={} #每个格子归属于第几个温度计，以及其现状
for i in range(len(thermometers)):
    for j in thermometers[i]:
        thermometers_dict[j]=[i,-1]

thermometers_in = [] #为了优化，描述每个温度计在哪些行列中
for i in thermometers:
    row_in=set()
    col_in=set()
    for j in i:
        row_in.add(j[0])
        col_in.add(j[1])
    thermometers_in.append((row_in,col_in))


minlen=[0]*len(thermometers)
maxlen=[len(i) for i in thermometers]
last_entropy = size**2 + 1
now_entropy = entropy()
while now_entropy < last_entropy:
    print(now_entropy)
    last_entropy = now_entropy

    for i in range(len(thermometers)):#正在考虑这个温度计
        min_i=minlen[i]
        max_i=maxlen[i]
        for j in range(minlen[i],maxlen[i]+1):#如果水银恰填充了j格
            full=thermometers[i][0:j]
            for row in thermometers_in[i][0]:#行是否有问题
                situation=[0,0,0]#0,1,-1
                for x in range(size):
                    if thermometers_dict[(row,x)][0]==i:
                        if (row,x) in full:
                            situation[1]+=1
                        else:
                            situation[0]+=1
                    else:
                        situation[thermometers_dict[(row,x)][1]]+=1
                if situation[0] > size - row_tasks[row]:#太白了
                    if j+1 > min_i:
                        min_i=j+1
                elif situation[1] > row_tasks[row]:#太红了
                    if j-1 < max_i:
                        max_i=j-1
            for col in thermometers_in[i][1]:#列是否有问题
                situation=[0,0,0]#0,1,-1
                for y in range(size):
                    if thermometers_dict[(y,col)][0]==i:
                        if (y,col) in full:
                            situation[1]+=1
                        else:
                            situation[0]+=1
                    else:
                        situation[thermometers_dict[(y,col)][1]]+=1
                if situation[0] > size - col_tasks[col]:#太白了
                    if j+1 > min_i:
                        min_i=j+1
                elif situation[1] > col_tasks[col]:#太红了
                    if j-1 < max_i:
                        max_i=j-1
        if min_i > minlen[i]:
            for k in thermometers[i][minlen[i]:min_i]:
                thermometers_dict[k][1]=1
            minlen[i] = min_i
        if max_i < maxlen[i]:
            for k in thermometers[i][max_i:maxlen[i]]:
                thermometers_dict[k][1]=0
            maxlen[i] = max_i
    now_entropy = entropy()

if minlen == maxlen:
    print('成功找出唯一解！')
else:
    print('未收敛……')

show_thermometers(size, row_tasks, col_tasks, thermometers, minlen, maxlen)