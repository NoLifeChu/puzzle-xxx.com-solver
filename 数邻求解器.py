from itertools import product
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from collections import defaultdict
from playwright.sync_api import sync_playwright

def fetch_dominosa(url="https://www.puzzle-dominosa.com/"):
    """
    输入 puzzle-dominosa 网页链接（支持每日、每周、每月等任意尺寸页面），
    后台静默抓取并直接返回 (height, width, grid)
    """
    print(f"正在后台启动无头浏览器抓取 Dominosa 页面: {url} ...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")

        # 核心等待：等棋盘所有格子渲染就位
        page.wait_for_selector("#game .cell", timeout=15000)

        # 将经过实战验证的绝对坐标归一化脚本注入后台浏览器
        result = page.evaluate("""() => {
            // 1. 获取所有绝对定位的格子
            let cells = Array.from(document.querySelectorAll('#game .cell'));
            if (cells.length === 0) {
                cells = Array.from(document.querySelectorAll(
                    '#puzzleContainer .cell, [id*="puzzle"] .cell, .board-back ~ div[class*="cell"]'
                ));
            }

            // 2. 提取坐标与数值
            const extracted = cells.map(c => {
                const span = c.querySelector('span');
                let val = span ? parseInt(span.textContent.trim(), 10) : NaN;
                if (isNaN(val)) {
                    const m = c.className.match(/cell(\\d+)/);
                    if (m) val = parseInt(m[1], 10);
                }
                return {
                    top: parseInt(c.style.top, 10),
                    left: parseInt(c.style.left, 10),
                    val: val
                };
            }).filter(d => !isNaN(d.val) && !isNaN(d.top) && !isNaN(d.left));

            if (extracted.length === 0) {
                return { error: "未找到任何格子，请检查页面是否已加载完毕。" };
            }

            // 3. 根据 top / left 的最小正差值，动态计算每格宽高
            const uniqSort = arr => [...new Set(arr)].sort((a, b) => a - b);
            const tops = uniqSort(extracted.map(d => d.top));
            const lefts = uniqSort(extracted.map(d => d.left));

            let cellH = 0, cellW = 0;
            for (let i = 1; i < tops.length; i++) {
                const diff = tops[i] - tops[i - 1];
                if (diff > 0) { cellH = diff; break; }
            }
            for (let i = 1; i < lefts.length; i++) {
                const diff = lefts[i] - lefts[i - 1];
                if (diff > 0) { cellW = diff; break; }
            }
            if (!cellH || !cellW) {
                const inner = cells[0] ? cells[0].querySelector('div') : null;
                if (inner) {
                    if (!cellH) cellH = parseInt(inner.style.height, 10) || 22;
                    if (!cellW) cellW = parseInt(inner.style.width, 10) || 22;
                }
                if (!cellH) cellH = 22;
                if (!cellW) cellW = 22;
            }

            // 4. 计算行列数并填装二维数组
            const rows = Math.round(Math.max(...extracted.map(d => d.top)) / cellH) + 1;
            const cols = Math.round(Math.max(...extracted.map(d => d.left)) / cellW) + 1;

            const grid = Array.from({length: rows}, () => Array(cols).fill(0));
            extracted.forEach(d => {
                const r = Math.round(d.top / cellH);
                const c = Math.round(d.left / cellW);
                if (r >= 0 && r < rows && c >= 0 && c < cols) grid[r][c] = d.val;
            });

            return { height: rows, width: cols, grid: grid };
        }""")

        browser.close()

        if result.get("error"):
            raise RuntimeError(result["error"])

        print(f"✔ 抓取成功！识别尺寸: {result['height']} 行 x {result['width']} 列")
        return result["height"], result["width"], result["grid"]


def visualize_puzzle(width, height, grid, bigdict, nodict):
    """
    可视化谜题求解进度。

    参数:
        width, height: 网格宽高
        grid: 二维列表，grid[i][j] 为对应数字
        bigdict: 字典，(i,j) -> -1（未配对）或 >=0（配对编号）
        nodict: 字典，(i,j) -> [左,右,上,下] 的 True/False 列表
                当两个相邻格子的对应边界均为 False 时，绘制红线
    """
    fig, ax = plt.subplots(figsize=(width * 0.6, height * 0.6))
    ax.set_xlim(-0.5, width - 0.5)
    ax.set_ylim(height - 0.5, -0.5)
    ax.set_aspect('equal')
    ax.axis('off')

    # ---------- 1. 按配对编号分组 ----------
    pairs = defaultdict(list)
    for (i, j), val in bigdict.items():
        if val >= 0:
            pairs[val].append((i, j))

    # 记录哪些坐标已被配对（用于决定文字颜色）
    paired_cells = set()
    for coords in pairs.values():
        for coord in coords:
            paired_cells.add(coord)

    # ---------- 2. 绘制配对背景（圆角黑条）----------
    for pair_id, coords in pairs.items():
        if len(coords) != 2:
            continue
        (r1, c1), (r2, c2) = coords
        margin = 0.38

        if r1 == r2:          # 横向连接
            row = r1
            col_start = min(c1, c2)
            x = col_start - margin
            y = row - margin
            w = 2.0 * margin + 1.0
            h = 2.0 * margin
        elif c1 == c2:        # 纵向连接
            col = c1
            row_start = min(r1, r2)
            x = col - margin
            y = row_start - margin
            w = 2.0 * margin
            h = 2.0 * margin + 1.0
        else:
            continue          # 非四相邻，跳过

        rect = FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.22",
            facecolor='#111111',
            edgecolor='none',
            alpha=0.95,
            zorder=1
        )
        ax.add_patch(rect)

    # ---------- 3. 绘制“不可能结合”红线 ----------
    # 水平相邻（左右之间）：当前格子的右 + 右侧格子的左 均为 False
    for i, j in product(range(height), range(width - 1)):
        if (not nodict[(i, j)][1]) and (not nodict[(i, j + 1)][0]):
            # 在 x=j+0.5 处画一条垂直红线，长度略小于 1
            ax.plot([j + 0.5, j + 0.5], [i - 0.4, i + 0.4],
                    color='red', linewidth=2.2, zorder=3, solid_capstyle='round')

    # 垂直相邻（上下之间）：当前格子的下 + 下方格子的上 均为 False
    for i, j in product(range(height - 1), range(width)):
        if (not nodict[(i, j)][3]) and (not nodict[(i + 1, j)][2]):
            # 在 y=i+0.5 处画一条水平红线，长度略小于 1
            ax.plot([j - 0.4, j + 0.4], [i + 0.5, i + 0.5],
                    color='red', linewidth=2.2, zorder=3, solid_capstyle='round')

    # ---------- 4. 绘制数字 ----------
    for i, j in product(range(height), range(width)):
        num = grid[i][j]
        # 已被黑框框住的数字改为白色，否则黑色
        color = 'white' if (i, j) in paired_cells else 'black'
        ax.text(
            j, i, str(num),
            ha='center', va='center',
            fontsize=11,
            color=color,
            fontweight='bold',
            zorder=2
        )

    plt.tight_layout(pad=0.2)
    plt.show()


def number_1(i,j,i1,j1):#弱化封装，返回二者的数字组合
    if bigdict[(i,j)]+bigdict[(i1,j1)]>-2:#至少一个已经有主了
        return#使用“卫语句”，扁平化提高可读性
    a=grid[i][j]
    b=grid[i1][j1]
    if a>b:
        a,b=b,a
    return (a,b)

def number(i,j,i1,j1):#封装
    loc=number_1(i,j,i1,j1)
    if not loc is None:
        if temdict[loc]==0:
            temdict[loc]=((i,j),(i1,j1))
        elif temdict[loc]!=-1:#即元组
            temdict[loc]=-1

def effect(loc1,loc2,com):#结算，顺便玩effect梗
    global order
    comdict[com]=True
    #把对应格子周围标为不可行
    for s in (loc1,loc2):
        bigdict[s]=order #nodict停止维护，此后这些格子的nodict可能是任意的
        if s[0]<height-1:
            nodict[(s[0]+1,s[1])][2]=False#下面格子的上方为False
        if s[0]>0:
            nodict[(s[0]-1,s[1])][3]=False
        if s[1]<width-1:
            nodict[(s[0],s[1]+1)][0]=False
        if s[1]>0:
            nodict[(s[0],s[1]-1)][1]=False
    order+=1
    #让对应数字组合的组合不可行
    for i, j in product(range(height), range(width)):#扫描每个格子周围
        if i<height-1:
            combine=number_1(i,j,i+1,j)
            if combine==com:
                nodict[(i,j)][3]=False
                nodict[(i+1,j)][2]=False
        if j<width-1:
            combine=number_1(i,j,i,j+1)
            if combine==com:
                nodict[(i,j)][1]=False
                nodict[(i,j+1)][0]=False

width=27
height=26
grid=[[15,1,5,10,10,12,14,6,1,8,13,19,10,5,13,1,17,6,3,14,22,10,15,22,18,1,9],[4,19,23,5,11,5,21,19,18,2,9,5,21,14,8,12,24,18,0,14,17,9,8,6,0,10,10],[13,8,25,4,13,13,8,6,25,14,25,5,0,6,22,12,12,16,16,25,8,6,16,11,25,23,6],[6,9,2,14,0,9,0,9,18,10,0,17,17,17,19,21,23,23,17,3,13,4,3,13,11,25,21],[4,15,10,1,8,9,5,21,11,2,14,11,12,12,17,21,15,0,24,21,0,25,4,0,5,20,22],[6,24,9,24,15,17,14,15,0,24,16,9,14,24,7,1,4,19,8,8,8,1,23,19,16,23,2],[10,8,7,16,22,7,11,6,22,10,10,15,16,11,8,17,18,20,23,23,25,13,7,8,3,20,15],[4,12,0,10,14,5,10,3,6,1,4,15,5,25,24,6,18,7,2,2,3,8,6,21,2,2,10],[17,12,22,4,14,22,13,17,23,12,17,14,7,18,8,7,8,24,7,22,16,15,16,3,14,6,0],[7,4,24,25,4,6,3,2,1,1,0,17,0,3,2,14,7,3,16,7,7,19,25,3,14,17,0],[0,20,24,17,20,5,18,15,20,15,25,22,22,21,21,19,15,18,20,21,23,3,15,22,11,1,8],[3,5,10,13,20,23,3,17,18,13,10,22,22,3,18,15,16,7,23,15,11,0,22,19,20,23,3],[20,9,2,7,21,5,15,15,20,10,17,4,3,22,14,24,18,18,2,2,11,19,9,11,17,11,5],[6,0,15,10,1,19,10,9,20,18,13,21,19,7,5,25,13,23,11,18,24,7,19,5,8,23,8],[24,20,22,11,2,17,6,21,8,12,25,14,7,7,9,7,12,4,12,12,10,16,16,24,5,5,4],[10,17,14,24,2,2,9,5,11,18,23,17,13,16,21,15,14,23,21,21,13,3,25,17,6,1,13],[16,5,14,16,24,1,4,16,9,8,4,2,25,0,24,0,1,24,1,5,11,9,12,2,11,21,11],[22,20,7,6,0,3,11,5,5,2,13,22,13,11,8,10,19,6,21,14,5,8,22,22,18,24,11],[20,14,9,11,9,7,24,16,12,18,24,0,4,23,18,23,2,12,23,6,19,13,15,19,19,19,14],[17,14,13,3,24,13,25,0,9,9,21,1,15,17,10,18,0,20,22,1,21,19,0,16,25,19,23],[19,16,20,1,21,4,12,9,14,20,14,7,8,0,4,15,4,18,4,22,14,18,6,4,13,9,3],[22,16,25,5,24,4,20,20,5,12,18,3,2,16,20,20,6,6,3,24,18,1,17,21,12,18,3],[25,17,7,2,12,6,1,5,2,11,1,21,22,12,8,7,1,16,4,4,18,16,20,8,25,25,10],[21,12,12,13,19,9,4,23,19,20,25,10,11,24,1,22,17,7,9,23,11,4,12,16,12,15,7],[19,15,25,16,1,23,2,20,2,21,25,23,20,9,9,18,10,12,15,13,20,19,19,0,22,3,11],
[24,6,24,19,6,25,13,1,9,3,23,13,13,25,2,12,23,3,21,11,7,10,15,1,16,8,2]]

height, width, grid = fetch_dominosa('https://cn.puzzle-dominosa.com/?size=10')


#数字范围：0~height-1，共height个数字

bigdict={}#键为坐标
for i, j in product(range(height), range(width)):
    bigdict[(i,j)]=-1#-1代表未结合；结合后按顺序赋值
nodict={}#键为坐标
for i, j in product(range(height), range(width)):
    nodict[(i,j)]=[True,True,True,True]#按顺序为左、右、上、下，表示是否有可能结合
    if i==0:
        nodict[(i,j)][2]=False
    if i==height-1:
        nodict[(i,j)][3]=False
    if j==0:
        nodict[(i,j)][0]=False
    if j==width-1:
        nodict[(i,j)][1]=False
comdict={}#键为数字组合
for i, j in product(range(height), range(height)):
        if i<=j:
            comdict[(i,j)]=False#还未占有

order=0
last_count=-1
while order>last_count:
    last_count=order
    #若全场只有这里有这个组合，组上
    temdict={}#键为数字组合
    for i, j in product(range(height), range(height)):
        if i<=j:
            if comdict[(i,j)]:#已经有了就直接判死刑
                temdict[(i,j)]=-1
            else:
                temdict[(i,j)]=0 #故技重施！0代表没找到（不可能）；元组代表只有一个；-1则是重复了
    for i, j in product(range(height), range(width)):#扫描每个格子周围
        if i<height-1:
            number(i,j,i+1,j)  
        if j<width-1:
            number(i,j,i,j+1)
            
    for i in temdict:
        if temdict[i]==0:
            print(f'出错！{i}组合未出现！')
        if type(temdict[i])==tuple:#找到！两个格子坐标是temdict[i][0]和temdict[i][1]；数字组合是i
            effect(temdict[i][0],temdict[i][1],i)
    #若这个格子四周只有一处能走，往这边走；即生命会自己找到出路
    for i in nodict:
        if bigdict[i]==-1:
            if nodict[i].count(True)==0:
                print(f'出错！{i}格子没有出路！')
            elif nodict[i].count(True)==1:#找到！两个格子坐标是i和j，数字组合是com
                if nodict[i][0]:#左
                    j=(i[0],i[1]-1)
                elif nodict[i][1]:
                    j=(i[0],i[1]+1)
                elif nodict[i][2]:
                    j=(i[0]-1,i[1])
                else:
                    j=(i[0]+1,i[1])
                com=number_1(i[0],i[1],j[0],j[1])
                effect(i,j,com)

#最后清洗一下nodict
for i in nodict:
    if bigdict[i]!=-1:
        if i[0]<height-1 and bigdict[(i[0]+1,i[1])]==bigdict[i]:#精心设计逻辑顺序，利用短路求值保安全
            nodict[i][3]=True
        elif i[0]>0 and bigdict[(i[0]-1,i[1])]==bigdict[i]:
            nodict[i][2]=True
        elif i[1]<width-1 and bigdict[(i[0],i[1]+1)]==bigdict[i]:
            nodict[i][1]=True
        else:
            nodict[i][0]=True

visualize_puzzle(width, height, grid, bigdict,nodict)