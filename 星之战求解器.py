from playwright.sync_api import sync_playwright
import tkinter as tk
import math

def fetch_star_battle(url="https://www.puzzle-star-battle.com/"):
    """
    抓取星之战题目，返回 (size, stars, regions)
    - size: 棋盘边长 N
    - stars: 每行/列/区要求的星星数量 (1, 2, 3, 4)
    - regions: N x N 的二维列表，每个格子的值为区域编号 (0 到 N-1)
    """
    print(f"正在后台启动无头浏览器抓取星之战题目: {url} ...")
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
            let height = sortedRowTops.length;
            let width = rowsMap.get(sortedRowTops[0]).length;

            let gridElements = [];
            for (let topKey of sortedRowTops) {
                let rowCells = rowsMap.get(topKey);
                rowCells.sort((a, b) => a.offsetLeft - b.offsetLeft);
                gridElements.push(rowCells);
            }

            function getColor(el) {
                for (let cls of el.classList) {
                    if (cls.startsWith('color-')) return cls;
                }
                return '';
            }

            function hasBorderRight(el) { return el.classList.contains('br'); }
            function hasBorderLeft(el) { return el.classList.contains('bl'); }
            function hasBorderBottom(el) { return el.classList.contains('bb'); }
            function hasBorderTop(el) { return el.classList.contains('bt'); }

            let regionMatrix = Array.from({length: height}, () => Array(width).fill(-1));
            let currentRegionId = 0;

            for (let r = 0; r < height; r++) {
                for (let c = 0; c < width; c++) {
                    if (regionMatrix[r][c] !== -1) continue;

                    let queue = [[r, c]];
                    let targetColor = getColor(gridElements[r][c]);
                    regionMatrix[r][c] = currentRegionId;

                    while (queue.length > 0) {
                        let [cr, cc] = queue.shift();
                        let currEl = gridElements[cr][cc];

                        if (cr + 1 < height && regionMatrix[cr + 1][cc] === -1) {
                            let nextEl = gridElements[cr + 1][cc];
                            if (!hasBorderBottom(currEl) && !hasBorderTop(nextEl) && getColor(nextEl) === targetColor) {
                                regionMatrix[cr + 1][cc] = currentRegionId;
                                queue.push([cr + 1, cc]);
                            }
                        }
                        if (cr - 1 >= 0 && regionMatrix[cr - 1][cc] === -1) {
                            let nextEl = gridElements[cr - 1][cc];
                            if (!hasBorderTop(currEl) && !hasBorderBottom(nextEl) && getColor(nextEl) === targetColor) {
                                regionMatrix[cr - 1][cc] = currentRegionId;
                                queue.push([cr - 1, cc]);
                            }
                        }
                        if (cc + 1 < width && regionMatrix[cr][cc + 1] === -1) {
                            let nextEl = gridElements[cr][cc + 1];
                            if (!hasBorderRight(currEl) && !hasBorderLeft(nextEl) && getColor(nextEl) === targetColor) {
                                regionMatrix[cr][cc + 1] = currentRegionId;
                                queue.push([cr, cc + 1]);
                            }
                        }
                        if (cc - 1 >= 0 && regionMatrix[cr][cc - 1] === -1) {
                            let nextEl = gridElements[cr][cc - 1];
                            if (!hasBorderLeft(currEl) && !hasBorderRight(nextEl) && getColor(nextEl) === targetColor) {
                                regionMatrix[cr][cc - 1] = currentRegionId;
                                queue.push([cr, cc - 1]);
                            }
                        }
                    }
                    currentRegionId++;
                }
            }

            let stars = 2;
            let infoEl = document.querySelector('.puzzleInfo');
            if (infoEl) {
                let text = infoEl.innerText.trim();
                // 核心正则：精准匹配紧挨着黑五角星的数字，如 "4★"
                let starMatch = text.match(/(\d+)\s*★/);
                if (starMatch) {
                    stars = parseInt(starMatch[1]);
                } else {
                    // 英文版兜底正则：匹配 "4 stars" 或 "4 star"
                    let engMatch = text.match(/(\d+)\s*star/i);
                    if (engMatch) stars = parseInt(engMatch[1]);
                }
            }
            let pageText = document.title + " " + document.body.innerText.slice(0, 500);

            return { size: width, regions: regionMatrix };
        }""")

        browser.close()
        print(f"✔ 星之战抓取成功！边长 {data['size']}x{data['size']}")
        return data["size"],data["stars"], data["regions"]

def show_star_battle(regions, grid):
    """
    星之战高保真可视化窗口:
    - regions: N x N 区域矩阵 (每个格为区域ID)
    - grid: N x N 状态矩阵 (-1 为空, 0 为打叉, 1 为星星)
    """
    size = len(regions)
    root = tk.Tk()
    root.title(f"Star Battle Visualization ({size}x{size})")

    # 根据尺寸自适应格子大小（控制在 750px 左右）
    cell_size = max(24, min(52, 760 // size))
    canvas_w = cell_size * size
    canvas_h = cell_size * size

    canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="#FFFFFF")
    canvas.pack(padx=15, pady=15)

    # 1. 柔和马卡龙区域调色板 (自动循环分配)
    PALETTE = [
        "#FFF2B2",  # 柔黄
        "#D4EBF7",  # 冰蓝
        "#E6D6F5",  # 淡紫
        "#D8F3DC",  # 薄荷绿
        "#FDD7DF",  # 浅樱粉
        "#FFE4C7",  # 杏桃色
        "#D7EEEC",  # 水绿
        "#F0E6D2"   # 浅米色
    ]

    # 绘制基础区域底色与细网格
    for r in range(size):
        for c in range(size):
            x1 = c * cell_size
            y1 = r * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size

            reg_id = regions[r][c]
            bg = PALETTE[reg_id % len(PALETTE)]
            canvas.create_rectangle(x1, y1, x2, y2, fill=bg, outline="#000000", width=1)

    # 2. 数学绘制黄金比例五角星 ⭐
    def draw_star(cx, cy, R):
        r_in = R * 0.42  # 黄金比例内凹半径
        points = []
        for i in range(10):
            angle = -math.pi / 2 + i * math.pi / 5
            radius = R if i % 2 == 0 else r_in
            points.extend([
                cx + radius * math.cos(angle),
                cy + radius * math.sin(angle)
            ])
        canvas.create_polygon(points, fill="#FFC800", outline="#B8860B", width=2)

    # 绘制打叉 ❌ (灰色细准星)
    def draw_cross(cx, cy, d):
        canvas.create_line(cx - d, cy - d, cx + d, cy + d, fill="#888888", width=2)
        canvas.create_line(cx - d, cy + d, cx + d, cy - d, fill="#888888", width=2)

    # 绘制盘面符号状态
    for r in range(size):
        for c in range(size):
            val = grid[r][c]
            cx = c * cell_size + cell_size / 2
            cy = r * cell_size + cell_size / 2

            if val == 1:
                draw_star(cx, cy, cell_size * 0.36)
            elif val == 0:
                draw_cross(cx, cy, cell_size * 0.18)

    # 3. 终层绘制：加粗区域黑边界 (置顶图层，保证边缘极其锋利)
    thick_w = 3.5
    for r in range(size):
        for c in range(size):
            x1 = c * cell_size
            y1 = r * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            reg = regions[r][c]

            # 上边界
            if r == 0 or regions[r - 1][c] != reg:
                canvas.create_line(x1, y1, x2, y1, fill="#1A1A1A", width=thick_w, capstyle=tk.PROJECTING)
            # 下边界
            if r == size - 1 or regions[r + 1][c] != reg:
                canvas.create_line(x1, y2, x2, y2, fill="#1A1A1A", width=thick_w, capstyle=tk.PROJECTING)
            # 左边界
            if c == 0 or regions[r][c - 1] != reg:
                canvas.create_line(x1, y1, x1, y2, fill="#1A1A1A", width=thick_w, capstyle=tk.PROJECTING)
            # 右边界
            if c == size - 1 or regions[r][c + 1] != reg:
                canvas.create_line(x2, y1, x2, y2, fill="#1A1A1A", width=thick_w, capstyle=tk.PROJECTING)

    root.mainloop()

def find_neigh(left_aim,location,egnar):
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
                    empty.append(find_neigh(left_aim,i,j))
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
                    empty.append(find_neigh(left_aim,i,j))
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
        if pair[0][0]+i[0]>=0 and pair[0][0]+i[0]<size and pair[0][1]+i[1]>=0 and pair[0][1]+i[1]<size:
            tian_location.append((pair[0][0]+i[0],pair[0][1]+i[1]))
    for i in pair:
        if i not in tian_location:
            return delta
    for i in tian_location:
        if i not in pair:
            if grid[i[0]][i[1]]==-1:
                grid[i[0]][i[1]]=0
                delta+=1
    return delta


def pairs_divide(aim,left_stars):
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
            grid[j[0]][j[1]]=0
        return 1
    return 0


#简单的谜题
size = 17
stars = 4
regions = [[0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1],[0,0,0,0,0,0,2,0,3,3,3,3,3,1,1,4,1],[5,5,5,5,5,2,2,2,3,2,3,1,1,1,4,4,1],[5,6,5,2,2,2,2,2,2,2,3,3,3,1,4,4,4],[5,6,2,2,2,2,2,2,2,2,7,7,1,1,4,4,4],[5,6,6,2,2,2,2,2,2,2,7,7,1,1,4,4,4],[8,6,6,6,2,6,2,6,2,7,7,7,1,1,4,4,4],[8,8,8,6,6,6,6,6,2,7,7,7,7,7,4,4,4],[9,9,8,8,8,8,8,10,11,7,7,7,12,7,7,4,4],[9,9,8,10,8,10,10,10,11,11,11,7,12,12,13,13,13],[9,9,9,10,10,10,10,11,11,14,11,14,14,12,12,13,13],[9,9,15,15,10,10,11,11,10,14,14,14,13,12,13,13,13],[9,9,9,15,9,10,10,10,10,10,10,14,13,12,12,12,13],[9,15,15,15,9,10,10,10,10,14,14,14,13,13,13,13,13],[9,9,9,15,9,9,10,16,16,14,16,14,13,13,13,13,13],[9,9,9,15,9,9,16,16,16,16,16,16,16,13,13,13,13],[9,9,9,9,9,9,9,9,16,16,16,16,16,16,13,13,13]]

#困难的谜题
size = 17
stars = 4
regions = [[0,1,1,1,1,1,1,1,1,2,2,2,2,2,3,3,3],[0,1,1,1,1,1,1,1,4,4,4,5,5,2,3,3,3],[0,0,0,1,4,4,4,4,4,4,4,5,5,2,3,3,3],[0,0,0,0,4,4,6,4,4,4,5,5,5,2,3,3,3],[0,0,0,0,4,4,6,4,4,4,4,5,7,7,7,7,3],[0,0,0,0,6,6,6,4,4,5,5,5,7,7,7,7,3],[0,0,8,0,0,0,6,6,6,5,5,5,7,7,7,3,3],[8,0,8,0,0,0,9,9,5,5,5,5,7,7,7,3,3],[8,8,8,8,8,8,9,10,10,5,5,5,5,7,3,3,3],[11,11,9,9,9,9,9,9,10,5,5,5,5,5,12,3,12],[11,9,9,9,9,9,9,10,10,10,10,13,13,13,12,12,12],[11,11,9,9,9,9,9,9,14,14,10,15,13,13,13,12,12],[11,9,9,9,9,9,9,14,14,10,10,15,13,13,13,13,12],[11,11,9,9,9,9,9,14,14,14,15,15,15,13,13,13,12],[11,9,9,9,16,16,16,14,15,15,15,14,13,13,13,13,13],[11,9,16,9,16,14,14,14,14,14,14,14,13,13,13,13,13],[16,16,16,16,16,14,14,14,14,14,14,14,14,13,13,13,13]]

size,stars,regions=fetch_star_battle(url="https://cn.puzzle-star-battle.com/?size=9")
print(stars)

grid = [[-1]*size for _ in range(size)]
divided=set()#(类别,编号)
pairs=[]

#grid[4][14]=0

effect=1
while effect>0:
    effect=0
    for i in range(size):#区域考虑
        if (2,i) not in divided:#还活着
            aim=[]#包含这个宫格所有活着的坐标元组
            left_stars=stars
            for y in range(size):
                for x in range(size):
                    if regions[y][x]==i and grid[y][x]==-1:
                        aim.append((y,x))
                    if regions[y][x]==i and grid[y][x]==1:
                        left_stars-=1
            divide_result=divide(aim,left_stars)
            if divide_result:#成功分割
                divided.add((2,i))
                for j in divide_result:
                    pairs.append(j)
            else:#是否存在数对
                effect+=pairs_divide(aim,left_stars)


    for y in range(size):#单行考虑
        if (0,y) not in divided:#还活着
            aim=[]#包含这个宫格所有活着的坐标元组
            left_stars=stars
            for x in range(size):
                if grid[y][x]==-1:
                    aim.append((y,x))
                if grid[y][x]==1:
                    left_stars-=1
            divide_result=divide(aim,left_stars)
            if divide_result:#成功分割
                divided.add((0,y))
                for j in divide_result:
                    pairs.append(j)
            else:
                effect+=pairs_divide(aim,left_stars)

    for x in range(size):#单列考虑
        if (1,x) not in divided:#还活着
            aim=[]#包含这个宫格所有活着的坐标元组
            left_stars=stars
            for y in range(size):
                if grid[y][x]==-1:
                    aim.append((y,x))
                if grid[y][x]==1:
                    left_stars-=1
            divide_result=divide(aim,left_stars)
            if divide_result:#成功分割
                divided.add((1,x))
                for j in divide_result:
                    pairs.append(j)
            else:
                effect+=pairs_divide(aim,left_stars)
    
    for y in range(size-1):#双行考虑
        if (3,y) not in divided:#还活着
            aim=[]#包含这个宫格所有活着的坐标元组
            left_stars=stars*2
            for x in range(size):
                if grid[y][x]==-1:
                    aim.append((y,x))
                if grid[y][x]==1:
                    left_stars-=1
                if grid[y+1][x]==-1:
                    aim.append((y+1,x))
                if grid[y+1][x]==1:
                    left_stars-=1
            divide_result=divide(aim,left_stars)
            if divide_result:#成功分割
                divided.add((3,y))
                for j in divide_result:
                    pairs.append(j)
            else:
                effect+=pairs_divide(aim,left_stars)

    for x in range(size-1):#双列考虑
        if (4,x) not in divided:#还活着
            aim=[]#包含这个宫格所有活着的坐标元组
            left_stars=stars*2
            for y in range(size):
                if grid[y][x]==-1:
                    aim.append((y,x))
                if grid[y][x]==1:
                    left_stars-=1
                if grid[y][x+1]==-1:
                    aim.append((y,x+1))
                if grid[y][x+1]==1:
                    left_stars-=1
            divide_result=divide(aim,left_stars)
            if divide_result:#成功分割
                divided.add((4,x))
                for j in divide_result:
                    pairs.append(j)
            else:
                effect+=pairs_divide(aim,left_stars)

    for i in pairs[:]:#最后处理方格对
        if len(i)==1:
            for y in (-1,0,1):
                for x in (-1,0,1):
                    if i[0][0]+y>=0 and i[0][0]+y<size and i[0][1]+x>=0 and i[0][1]+x<size:
                        grid[i[0][0]+y][i[0][1]+x]=0
            grid[i[0][0]][i[0][1]]=1
            effect+=1
            pairs.remove(i)
        else:
            if len(i)<4:
                effect+=tian_cover(i,[(-1,1),(-1,0),(0,1),(0,0)])
                effect+=tian_cover(i,[(-1,-1),(-1,0),(0,-1),(0,0)])
                effect+=tian_cover(i,[(1,-1),(1,0),(0,-1),(0,0)])
                effect+=tian_cover(i,[(1,1),(1,0),(0,1),(0,0)])
            i_del=0
            for j in i[:]:
                if grid[j[0]][j[1]]==0:
                    i.remove(j)
                    effect+=1
                if grid[j[0]][j[1]]==1:
                    i_del=1
            if i_del==1:
                pairs.remove(i)

    '''
    # 容量防御定理 (Overkill Elimination / 鸽巢过杀排斥)
    # 1. 扫描每一行，检查它上下的邻居
    for r in range(size):
        rem_stars = stars - grid[r].count(1)
        empty_in_row = [c for c in range(size) if grid[r][c] == -1]
        
        # 只有当这一行处于"高度紧绷"状态时触发 (剩下的空格没比缺的星星多几个)
        if len(empty_in_row) >= rem_stars > 0:
            # 检查直接挨着这一行的上一行 (r-1) 和 下一行 (r+1)
            for adj_r in (r - 1, r + 1):
                if 0 <= adj_r < size:
                    for adj_c in range(size):
                        # 如果邻居是个未决的空格
                        if grid[adj_r][adj_c] == -1:
                            # 算算看：如果在这个邻居放星星，会同时炸死当前行里的几个空格？
                            # (只要列坐标差值 <= 1，就会被八邻域辐射杀死)
                            killed = [c for c in empty_in_row if abs(c - adj_c) <= 1]
                            
                            # 💥 触发容量过杀！杀得太狠导致当前行连星数都凑不齐了！
                            if len(empty_in_row) - len(killed) < rem_stars:
                                grid[adj_r][adj_c] = 0  # 绿圈当场暴毙！填 0 (打叉 ❌)！
                                effect += 1

    # 2. 扫描每一列，检查它左右的邻居 (完全镜像对称！)
    for c in range(size):
        col_vals = [grid[r][c] for r in range(size)]
        rem_stars = stars - col_vals.count(1)
        empty_in_col = [r for r in range(size) if grid[r][c] == -1]
        
        if len(empty_in_col) >= rem_stars > 0:
            for adj_c in (c - 1, c + 1):
                if 0 <= adj_c < size:
                    for adj_r in range(size):
                        if grid[adj_r][adj_c] == -1:
                            killed = [r for r in empty_in_col if abs(r - adj_r) <= 1]
                            if len(empty_in_col) - len(killed) < rem_stars:
                                grid[adj_r][adj_c] = 0
                                effect += 1
    '''

show_star_battle(regions, grid)