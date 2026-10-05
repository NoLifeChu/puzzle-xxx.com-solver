from itertools import permutations
import tkinter as tk
from playwright.sync_api import sync_playwright
#抓取网页链接
def fetch_kakuro(url="https://www.puzzle-kakuro.com/"):
    """
    输入数和网页链接（支持每日、每周、每月等任意尺寸页面），
    后台静默抓取并直接返回 (height, width, grid)
    """
    print(f"正在后台启动无头浏览器抓取数和页面: {url} ...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        # 核心等待：等棋盘所有格子渲染就位
        page.wait_for_selector(".cell.selectable")

        # 将经过实战验证的绝对坐标归一化脚本注入后台浏览器
        data = page.evaluate("""() => {
            let cells = Array.from(document.querySelectorAll('.cell.selectable'));

            // 1. 按照物理像素坐标聚类成行 (5px 容差防抖动)
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

            // 2. 逐格提取类型
            let grid = [];
            for (let topKey of sortedRowTops) {
                let rowCells = rowsMap.get(topKey);
                rowCells.sort((a, b) => a.offsetLeft - b.offsetLeft);

                let rowData = [];
                for (let c of rowCells) {
                    let isWall = c.classList.contains('wall');
                    let isTask = c.classList.contains('task');

                    if (isTask) {
                        // 线索格：提取垂直向下 (v) 和 水平向右 (h)
                        let vEl = c.querySelector('.task-vertical');
                        let hEl = c.querySelector('.task-horizontal');
                        let v = vEl ? parseInt(vEl.innerText.trim()) : 0;
                        let h = hEl ? parseInt(hEl.innerText.trim()) : 0;
                        rowData.push([isNaN(v) ? 0 : v, isNaN(h) ? 0 : h]);
                    } else if (isWall) {
                        // 纯死黑墙：在 Python 里自动转为 None
                        rowData.push(null);
                    } else {
                        // 白格：可填区域，未填记为 0
                        let numEl = c.querySelector('.number');
                        let num = numEl ? parseInt(numEl.innerText.trim()) : 0;
                        rowData.push(isNaN(num) ? 0 : num);
                    }
                }
                grid.push(rowData);
            }

            return { height: height, width: width, grid: grid };
        }""")

        browser.close()
        print(f"✔ 抓取成功！识别尺寸: {data['height']} 行 x {data['width']} 列")
        return data["height"], data["width"], data["grid"]

#如果是常规尺寸，请仍手动使用抓取器并粘贴到下方，并将下方的自动抓取器注释掉


#
#如果是每日/周/月挑战，用这个
height, width, grid = fetch_kakuro("https://cn.puzzle-kakuro.com/?size=14")

#生成超雷霆Plus版四库全书Pro Max
biglist={}#(行/列格子数,和):((所有可能的排列，预计最多9!项，在key为(9,45)时取到))
for n in range(1,10):
    for s in range(int(n*(n+1)/2),int(n*(19-n)/2)+1):
        biglist[(n,s)]=[]
    for p in permutations(range(1, 10), n):
        biglist[(n,sum(p))].append(p)

#把提示降维成谁几个加起来等于几，无论横竖
task=[]
#先横
for i in range(height):
    for j in range(width):
        cell = grid[i][j]
        if isinstance(cell, list) and cell[1] > 0:
            cells=[]
            now_j=j+1
            #向右扫描
            while now_j < width and grid[i][now_j] == 0:
                cells.append((i, now_j))
                now_j += 1
            task.append([cells,cell[1]])
#后竖
for i in range(height):
    for j in range(width):
        cell = grid[i][j]
        if isinstance(cell, list) and cell[0] > 0:
            cells=[]
            now_i=i+1
            #向下扫描
            while now_i < height and grid[now_i][j] == 0:
                cells.append((now_i, j))
                now_i += 1
            task.append([cells,cell[0]])

#依旧候选数，但这次不同
candidates={}
for i in range(height):
    for j in range(width):
        cell = grid[i][j]
        if cell==0:
            candidates[(i,j)]=[1,2,3,4,5,6,7,8,9]

#开始筛选！
effect=1
while effect>0:
    effect=0
    for i in task[:]:#task:[[坐标元组],总和];加[:]防止遍历跳过
        #挂载相应的四库全书
        possibility=biglist[(len(i[0]),i[1])]
        for j in range(len(i[0])):#这一行/列的剩余个数
            possibility = [a for a in possibility if a[j] in candidates[i[0][j]]]
        for j in range(len(i[0])):
            if grid[i[0][j][0]][i[0][j][1]]!=0:
                continue
            values_at_j = {p[j] for p in possibility}
            for n in range(1,10):
                if (n in candidates[i[0][j]]) and (n not in values_at_j):#只需要统计都不出现，因为“只出现”会淘汰其他候选，从而通过唯一候选出数
                    effect+=1
                    candidates[i[0][j]].remove(n)
        dellist=[]
        for j in i[0]:
            if len(candidates[j])==1:
                result=candidates[j][0]
                grid[j[0]][j[1]]=result
                dellist.append(j)
        #重点！直接对task进行删减！
        for j in dellist:
            i[0].remove(j)
            i[1]-=candidates[j][0]
            
            #把有关条带删除
            for rem in i[0]:
                if candidates[j][0] in candidates[rem]:
                    print('你真是粗心')
                    candidates[rem].remove(candidates[j][0])
            
        if not i[0]:#你没用了，再见
            task.remove(i)



def show_kakuro(grid):
    height = len(grid)
    width = len(grid[0])
    
    root = tk.Tk()
    root.title(f"Kakuro Solver Visualization ({height}x{width})")

    # 根据屏幕自适应格子尺寸（40x40 时约 20px，保证能完整显示在屏幕内）
    max_dim = max(height, width)
    cell_size = max(16, min(36, 820 // max_dim))
    
    canvas_w = cell_size * width
    canvas_h = cell_size * height
    
    canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="#111111")
    canvas.pack(padx=10, pady=10)

    # 字体尺寸自适应
    main_font_size = max(8, int(cell_size * 0.58))
    clue_font_size = max(6, int(cell_size * 0.34))
    
    main_font = ("Consolas", main_font_size, "bold")
    clue_font = ("Arial", clue_font_size, "bold")

    for r in range(height):
        for c in range(width):
            x1 = c * cell_size
            y1 = r * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            
            cell = grid[r][c]
            
            if cell is None:
                # 1. 纯黑死墙
                canvas.create_rectangle(x1, y1, x2, y2, fill="#181818", outline="#2A2A2A", width=1)
            
            elif isinstance(cell, list):
                # 2. 线索格（深灰底 + 对角斜线切分）
                v_clue, h_clue = cell[0], cell[1]
                canvas.create_rectangle(x1, y1, x2, y2, fill="#2B2B36", outline="#3C3C48", width=1)
                canvas.create_line(x1, y1, x2, y2, fill="#555566", width=1)
                
                # 左下半区：垂直向下线索 (v)
                if v_clue > 0:
                    canvas.create_text(
                        x1 + cell_size * 0.28, 
                        y1 + cell_size * 0.72, 
                        text=str(v_clue), 
                        fill="#FFAA33",  # 暖橙色线索
                        font=clue_font
                    )
                # 右上半区：水平向右线索 (h)
                if h_clue > 0:
                    canvas.create_text(
                        x1 + cell_size * 0.72, 
                        y1 + cell_size * 0.28, 
                        text=str(h_clue), 
                        fill="#44DD66",  # 翠绿色线索
                        font=clue_font
                    )
            
            else:
                # 3. 白格（填数区）
                canvas.create_rectangle(x1, y1, x2, y2, fill="#FFFFFF", outline="#777777", width=1)
                if cell > 0:
                    canvas.create_text(
                        x1 + cell_size / 2, 
                        y1 + cell_size / 2, 
                        text=str(cell), 
                        fill="#0033CC",  # 答案用极其清晰的深宝石蓝
                        font=main_font
                    )

    root.mainloop()

# 在你求解结束后直接调用：
show_kakuro(grid)