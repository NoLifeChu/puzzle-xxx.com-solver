import itertools
import tkinter as tk
import math

def show_invisible_star_battle(grid):
    """
    无形星之战通用可视化窗口 (兼容暴力版与技巧版)
    grid 取值规范:
      1: 星星 ⭐
      0: 黑色障碍墙 ⬛
      2: 白格打叉 ❌
     -1: 未知白格 ⬜
    """
    size = len(grid)
    root = tk.Tk()
    root.title(f"Invisible Star Battle ({size}x{size})")

    # 根据尺寸自适应格子大小 (6x6~10x10 约 55~75px 一格)
    cell_size = max(35, min(75, 750 // size))
    canvas_w = cell_size * size
    canvas_h = cell_size * size

    canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="#FFFFFF")
    canvas.pack(padx=20, pady=20)

    # 1. 绘制底层网格与黑墙
    for r in range(size):
        for c in range(size):
            x1 = c * cell_size
            y1 = r * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size

            val = grid[r][c]

            if val == 0:
                # 物理黑墙：深黑实体方块
                canvas.create_rectangle(x1, y1, x2, y2, fill="#18181A", outline="#333338", width=1.5)
            else:
                # 白格：纯白底 + 浅灰细网格线
                canvas.create_rectangle(x1, y1, x2, y2, fill="#FFFFFF", outline="#CCCCCC", width=1)

    # 2. 数学绘制五角星 ⭐ 与打叉 ❌
    def draw_star(cx, cy, R):
        r_in = R * 0.42
        points = []
        for i in range(10):
            angle = -math.pi / 2 + i * math.pi / 5
            radius = R if i % 2 == 0 else r_in
            points.extend([
                cx + radius * math.cos(angle),
                cy + radius * math.sin(angle)
            ])
        canvas.create_polygon(points, fill="#FFC800", outline="#B8860B", width=2)

    def draw_cross(cx, cy, d):
        canvas.create_line(cx - d, cy - d, cx + d, cy + d, fill="#888888", width=2)
        canvas.create_line(cx - d, cy + d, cx + d, cy - d, fill="#888888", width=2)

    # 绘制格内符号
    for r in range(size):
        for c in range(size):
            val = grid[r][c]
            cx = c * cell_size + cell_size / 2
            cy = r * cell_size + cell_size / 2

            if val == 1:
                draw_star(cx, cy, cell_size * 0.36)
            elif val == 2:
                draw_cross(cx, cy, cell_size * 0.18)

    # 3. 压上加粗的棋盘外边框
    canvas.create_rectangle(2, 2, canvas_w, canvas_h, outline="#18181A", width=3)

    root.mainloop()

def turn_tuple_bits(size,t):
    re=0
    for i in range(size):
        re= re | (1 << (i * size + t[i]))
    return re

def turn_bits_location(size,t):
    answer=[[-1]*size for _ in range(size)]
    bit=0
    while t > 0:
        if t % 2 ==1:
            answer[bit//size][bit%size]=1
        bit+=1
        t = t >> 1

    return answer

def turn_tuple_bits2(size,t):
    re=0
    for i in range(size):
        for j in t[i]:
            re= re | (1 << (i * size + j))
    return re

def dp(size,r,situation):
    if r==0:
        result=[]
        states = [(a, b) for a in range(size) for b in range(a + 2, size)]
        for i in states:
            if (r,i[0]) not in walls and (r,i[1]) not in walls:
                d=dp(size,r+1,situation+[i])
                if d:
                    result = result + d
        return result
    elif r==size:
        return [turn_tuple_bits2(size,situation)]
    else:
        result=[]
        used=[2]*size
        for i in situation:
            for j in i:
                used[j]-=1
        useful=[]
        for i in range(size):
            if used[i]>0:
                useful.append(i)
        for i in situation[-1]:
            for j in useful[:]:
                if -1<=i-j<=1:
                    useful.remove(j)
        states = [(a, b) for a in useful for b in useful if a+1<b]
        for i in states:
            if (r,i[0]) not in walls and (r,i[1]) not in walls:
                d=dp(size,r+1,situation+[i])
                if d:
                    result = result + d
        return result


def pre_count(size,stars):
    if stars==1:
        valid = []
        for p in itertools.permutations(range(size)):
            if all(abs(p[i] - p[i+1]) >= 2 for i in range(size-1)):
                valid.append(turn_tuple_bits(size,p))
        return valid
    elif stars==2:#我要放大招了
        valid = dp(size,0,[])
        return valid

    else:#超规模就不奉陪了
        return []


# 无形的星之战 题号: 4,853,387
size = 10
stars = 2
grid = [[-1,-1,-1,-1,-1,-1,-1,-1,-1,-1],[0,-1,-1,0,0,0,-1,-1,0,-1],[-1,0,0,-1,0,-1,-1,-1,-1,0],[-1,-1,0,0,-1,-1,-1,-1,0,0],[-1,-1,0,-1,-1,-1,-1,-1,-1,-1],[-1,-1,0,-1,-1,-1,0,-1,-1,-1],[-1,-1,-1,-1,-1,-1,-1,-1,-1,-1],[-1,-1,0,-1,-1,-1,0,-1,-1,-1],[-1,0,0,-1,-1,-1,-1,-1,-1,-1],[-1,-1,0,-1,-1,-1,-1,-1,0,-1]]
walls = ((1,0),(1,3),(1,4),(1,5),(1,8),(2,1),(2,2),(2,4),(2,9),(3,2),(3,3),(3,8),(3,9),(4,2),(5,2),(5,6),(7,2),(7,6),(8,1),(8,2),(9,2),(9,8))





all_answer=pre_count(size,stars)
print(len(all_answer))
answer=[]

grid_bits=0
for i in range(size):
    for j in range(size):
        if grid[i][j]==0:
            grid_bits=grid_bits| (1 << (i * size + j))
for i in all_answer:
    if i & grid_bits==0:
        answer=turn_bits_location(size,i)

# 暴力求解器星星搬运工：把 answer(1/-1) 融合进已包含黑墙(0)的 grid 中
for r in range(size):
    for c in range(size):
        if answer[r][c] == 1:
            grid[r][c] = 1  # 填入真·五角星 ⭐
        elif grid[r][c] == -1:
            grid[r][c] = 2  # 其余不是黑墙的白格，全部打叉 ❌

show_invisible_star_battle(grid)