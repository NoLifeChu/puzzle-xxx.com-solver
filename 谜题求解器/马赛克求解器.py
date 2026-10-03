def find_near(a) : #返回包含所有相邻坐标元组的列表
    res=[]
    for i in range(a[0]-1, a[0]+2):
        if 0<=i<size:
            for j in range(a[1]-1, a[1]+2):
                if 0<=j<size:
                    res.append((i, j))
    return res

def count(a): #统计特定列表或集合的未知、白、黑数量，返回三项的列表
    situation=[0,0,0]
    for i in a:
        situation[answer[i[0]][i[1]]+1]+=1
    return(situation)

def nearself(a): #若自身周围未填格只能为全黑或全白，填满；难度系数1.0
    neigh=find_near(a)
    clue=task[a[0]][a[1]]
    if clue is None:
        return 0
    situation=count(neigh)
    if situation[0]==0:
        return 0
    if situation[2]==clue: #黑格满了，未知当然只能全部填白色
        #开始修改answer
        for i in neigh:
            if answer[i[0]][i[1]]==-1:
                answer[i[0]][i[1]]=0
        return 1
    if situation[0]+situation[2]==clue: #未知只能全部填黑色
        #开始修改answer
        for i in neigh:
            if answer[i[0]][i[1]]==-1:
                answer[i[0]][i[1]]=1
        return 2
    return 0

def diff(a,b): #两格差分
    a_number=task[a[0]][a[1]]
    b_number=task[b[0]][b[1]]
    if a_number is None or b_number is None : #仅当ab都有数字时有效
        return 0
    a_near=set(find_near(a))
    b_near=set(find_near(b))
    public=a_near & b_near
    if not public: #理论上不会传入无公共的ab，仅边界处理
        return 0
    a_pri=a_near-public
    b_pri=b_near-public
    situation_a_pri=count(a_pri)
    situation_b_pri=count(b_pri)
    if situation_a_pri[0]+situation_b_pri[0]==0: #私有没有未知还比个啥
        return 0
    if situation_a_pri[0]+situation_a_pri[2]-situation_b_pri[2] == a_number-b_number: #必须将a涂黑，将b涂白
        #开始修改answer
        for i in a_pri:
            if answer[i[0]][i[1]]==-1:
                answer[i[0]][i[1]]=1
        for i in b_pri:
            if answer[i[0]][i[1]]==-1:
                answer[i[0]][i[1]]=0
        return 1
    if situation_b_pri[0]+situation_b_pri[2]-situation_a_pri[2] == b_number-a_number: #必须将b涂黑，将a涂白
        #开始修改answer
        for i in b_pri:
            if answer[i[0]][i[1]]==-1:
                answer[i[0]][i[1]]=1
        for i in a_pri:
            if answer[i[0]][i[1]]==-1:
                answer[i[0]][i[1]]=0
        return 1
    return 0

def near4(a): #四相邻最易发现也最实用，难度系数2.0
    effect1=0
    if a[0]<size-1: #和下面比
        b=(a[0]+1,a[1])
        effect1 +=diff(a,b)
    if a[1]<size-1: #和右边比
        b=(a[0],a[1]+1)
        effect1 +=diff(a,b)
    return effect1

def near8(a): #其次是对角相邻，难度系数2.5
    effect1=0
    if a[1]<size-1 and a[0]>0: #和右上比
        b=(a[0]-1,a[1]+1)
        effect1 +=diff(a,b)
    if a[1]<size-1 and a[0]<size-1: #和右下比
        b=(a[0]+1,a[1]+1)
        effect1 +=diff(a,b)
    return effect1

def near44(a): #隔格相邻再难一点，难度系数2.6
    effect1=0
    if a[0]<size-2: #和下下比
        b=(a[0]+2,a[1])
        effect1 +=diff(a,b)
    if a[1]<size-2: #和右右比
        b=(a[0],a[1]+2)
        effect1 +=diff(a,b)
    return effect1

#
task=[[2,4,3,None,0,None,None,None,None,3,None,2,2,3,None,None,2,None,None,None,None,3,1,None,1,None,1,1,1,None,None,None,None,3,None,2,None,None,None,2,None,5,None,5,3,1,None,0,None,2],[None,5,3,None,None,None,3,None,None,6,None,3,3,None,None,4,3,3,5,8,5,4,None,3,3,3,4,4,None,1,None,3,None,None,5,None,2,0,None,4,7,7,None,None,6,None,None,2,3,3],[3,None,None,None,None,3,5,None,None,7,None,5,4,None,None,3,2,2,4,7,5,5,None,4,None,None,4,4,3,None,3,None,None,5,6,4,2,None,5,None,6,None,None,6,6,None,None,None,None,2],[None,4,None,None,7,6,7,5,7,None,None,5,None,None,None,None,3,3,5,None,None,5,None,None,None,None,4,None,None,None,None,3,None,5,None,6,5,4,None,None,None,None,None,6,None,None,None,5,5,None],[4,None,None,None,None,5,6,None,None,4,None,None,None,None,None,5,None,3,None,6,5,4,3,None,None,4,None,None,3,5,3,None,None,None,5,4,None,None,None,6,7,None,None,5,None,6,None,6,6,None],[None,4,4,4,4,None,None,None,None,None,None,None,None,7,6,6,3,5,6,7,5,3,None,None,5,None,None,None,None,None,None,None,None,None,None,None,None,None,5,None,None,6,None,None,5,4,4,5,None,None],[None,4,4,3,None,None,None,None,6,6,3,None,2,None,None,5,2,None,None,None,None,None,2,None,None,5,5,4,None,None,None,None,3,4,5,None,None,3,None,4,None,5,5,None,None,4,3,None,None,None],[None,1,None,None,3,3,None,None,4,5,None,None,3,6,4,None,None,4,5,5,4,2,None,None,None,None,None,3,2,None,1,3,4,7,8,8,None,5,4,4,None,None,5,None,2,1,1,None,4,None],[2,4,6,None,5,None,None,None,6,None,3,2,None,None,3,3,None,None,4,3,3,None,2,2,None,None,None,5,5,3,None,2,None,5,7,6,None,5,None,None,None,None,None,4,None,None,None,3,6,None],[None,None,5,3,None,1,3,3,None,None,None,3,None,4,4,None,None,5,None,None,None,3,2,None,None,None,2,3,5,4,None,None,None,None,None,6,6,6,None,None,None,4,None,3,None,1,None,None,5,3],[None,8,None,None,4,4,None,None,None,None,None,4,4,None,None,None,5,7,None,None,None,3,3,3,None,None,None,3,None,6,5,None,5,None,5,3,None,None,None,None,3,None,None,None,2,None,3,None,3,None],[None,None,None,3,3,4,None,None,3,4,None,None,None,3,4,4,7,None,6,None,2,3,None,None,None,4,None,3,4,5,None,None,None,7,6,None,None,None,4,None,5,None,None,None,None,3,None,None,3,2],[None,None,None,None,4,None,None,6,3,None,None,7,None,4,3,4,6,None,7,4,None,None,None,5,None,5,4,3,3,None,None,8,7,4,3,None,5,None,None,3,6,None,6,None,None,6,None,None,3,None],[2,3,None,2,None,None,7,6,3,None,None,None,4,2,2,None,None,8,8,5,None,None,None,None,None,5,3,None,3,None,6,None,None,None,None,5,None,None,None,2,None,None,4,None,5,None,4,None,4,4],[2,None,3,4,None,6,None,5,3,None,None,None,None,None,2,None,5,None,None,None,4,None,None,5,None,5,None,None,None,None,4,None,3,3,None,4,None,4,None,1,None,4,None,6,None,None,None,1,2,None],[1,4,None,7,None,6,5,None,None,None,4,None,None,2,None,4,5,6,6,None,None,2,None,None,6,5,3,None,None,3,4,None,None,None,1,None,4,4,3,None,None,6,None,7,4,None,2,None,2,None],[None,2,4,7,7,7,None,None,None,6,3,1,2,2,None,5,None,None,None,None,None,None,5,6,None,None,None,None,3,None,4,None,None,4,1,3,4,None,None,None,None,7,5,None,None,4,2,3,None,None],[1,None,None,None,None,7,5,6,None,7,4,1,2,None,None,None,None,None,None,None,6,None,4,4,None,5,None,4,4,1,3,None,5,None,None,2,2,4,None,None,4,None,None,6,3,3,None,4,4,2],[None,None,None,None,5,None,None,4,None,None,None,None,2,None,3,None,4,None,None,7,6,5,4,4,None,None,6,6,None,3,None,None,6,None,4,None,4,None,None,None,None,5,3,3,2,None,None,4,5,4],[None,None,8,7,4,None,None,None,None,6,None,4,None,3,None,4,None,None,None,None,5,None,None,None,4,None,7,None,None,None,6,None,None,None,None,3,None,None,None,None,None,4,None,None,4,4,None,5,None,4],[3,6,6,None,None,5,None,None,None,None,None,None,None,5,5,6,None,None,None,None,None,4,3,None,None,None,6,6,5,6,None,7,None,None,None,None,None,None,None,4,6,5,5,None,None,None,None,None,4,None],[4,None,None,5,None,6,7,7,8,7,6,None,6,None,7,None,7,None,None,6,None,None,2,None,None,None,3,3,None,3,None,None,6,5,None,None,5,None,4,None,None,None,5,5,None,None,None,None,3,None],[None,3,None,None,None,7,None,8,8,6,None,None,5,None,None,6,6,None,None,4,4,7,5,6,3,None,1,2,None,1,3,6,None,None,4,7,6,3,1,3,6,6,5,4,4,3,None,None,None,1],[2,3,None,None,None,None,None,5,None,3,4,None,None,None,None,3,None,None,3,3,3,5,4,5,None,None,3,2,None,None,2,None,None,None,None,6,None,None,None,None,4,4,4,3,4,4,5,5,5,3],[None,None,2,3,5,6,None,5,None,None,None,None,None,None,None,1,3,None,4,3,None,6,None,5,None,None,4,None,None,2,3,3,5,None,5,5,None,4,3,3,None,None,None,None,6,6,6,None,None,None],[0,None,4,None,None,3,None,4,None,5,6,None,None,4,3,None,None,None,None,None,None,None,6,None,6,None,6,None,4,3,None,None,None,None,None,4,3,None,None,None,None,None,None,6,None,None,None,None,5,4],[2,None,None,None,5,None,4,None,None,6,None,5,5,3,4,None,None,None,None,None,8,None,None,6,None,None,4,None,None,5,None,None,None,6,5,4,None,None,6,6,None,4,None,None,None,6,None,4,None,4],[None,4,6,None,6,3,3,4,6,None,7,None,None,6,7,None,None,3,None,None,None,None,None,5,None,None,None,None,5,5,None,5,None,5,3,2,2,5,None,7,None,5,None,None,5,None,None,None,4,3],[4,None,5,6,None,None,None,4,6,5,None,None,None,None,None,None,None,1,None,2,2,3,None,6,4,None,None,None,None,None,4,4,7,7,6,None,None,5,5,6,None,None,6,None,7,6,5,None,4,None],[None,4,6,None,7,5,None,None,None,None,None,4,4,None,None,None,3,None,None,None,None,4,None,None,5,None,None,5,3,None,5,6,8,6,None,None,None,5,None,None,None,7,None,8,8,None,6,6,5,3],[None,None,None,None,4,3,None,None,3,3,3,None,2,4,None,5,None,None,None,None,4,5,7,None,6,None,None,4,3,4,6,None,None,None,7,7,None,None,None,4,5,None,7,None,None,7,8,None,None,4],[None,None,None,4,4,3,5,None,None,None,None,None,4,None,None,2,3,None,6,None,6,None,None,8,None,None,None,None,4,6,None,7,6,None,5,5,7,None,4,3,None,6,None,6,None,7,None,6,7,4],[None,4,None,3,3,None,None,None,5,None,None,6,None,3,1,None,None,5,5,6,6,None,5,None,None,None,None,None,None,None,7,None,None,None,None,None,7,None,5,None,4,3,4,None,6,6,8,None,None,None],[4,None,3,None,4,None,None,7,6,7,None,7,None,5,3,None,3,None,None,None,None,None,None,None,5,None,None,7,None,None,None,6,3,1,None,3,6,None,5,2,4,None,5,None,7,7,None,6,5,2],[None,None,2,None,2,None,None,None,None,8,8,None,7,None,4,4,3,6,None,None,None,None,None,None,6,None,6,4,4,5,None,None,None,3,3,None,None,None,None,None,None,None,3,3,5,4,None,5,4,2],[None,6,3,1,None,None,None,6,5,7,6,7,None,None,3,None,2,5,4,4,1,None,None,5,6,4,4,3,None,None,None,None,3,4,2,1,3,5,7,None,None,None,5,5,5,None,None,4,3,1],[None,5,3,1,2,4,None,6,None,None,4,4,2,None,3,3,None,None,None,2,None,2,None,7,None,None,4,4,None,6,None,None,None,4,3,None,None,None,None,4,None,5,5,None,None,None,None,3,None,None],[None,5,4,None,None,None,None,6,3,None,None,2,None,3,4,4,None,None,2,1,2,2,5,None,None,None,3,4,6,6,None,None,None,None,None,2,4,None,None,4,None,4,None,None,None,None,None,2,3,1],[None,5,5,4,None,None,None,None,None,3,None,None,None,None,6,None,None,None,None,None,None,None,None,None,None,3,2,2,None,6,7,4,None,None,None,3,None,None,None,4,4,None,4,None,3,None,4,None,None,3],[5,8,7,6,3,None,None,None,None,3,2,None,None,6,6,None,None,4,None,2,2,3,6,None,None,2,1,2,4,None,6,3,None,2,5,4,None,4,7,None,5,4,None,None,None,None,None,None,7,None],[3,None,None,6,4,5,5,None,None,None,3,None,7,6,None,4,None,None,3,None,None,None,None,None,None,5,4,4,4,None,6,4,3,None,None,None,None,5,None,6,5,None,None,None,None,1,2,None,None,None],[3,4,None,None,None,4,4,None,None,2,None,3,4,5,None,None,None,None,None,1,None,2,3,4,6,None,None,None,None,None,None,None,4,2,None,4,None,6,None,None,None,None,4,5,3,2,2,None,None,6],[3,3,4,None,7,None,None,3,None,5,6,5,None,None,3,6,5,5,2,2,4,None,None,2,5,7,None,None,3,2,None,None,None,5,None,None,None,6,None,None,None,2,None,None,4,None,None,6,None,None],[None,5,4,None,None,None,None,None,3,None,5,None,None,None,4,5,None,4,2,None,None,None,None,3,None,4,None,None,None,None,3,None,6,4,6,None,7,None,6,4,3,4,3,4,4,7,None,None,5,None],[None,None,None,None,5,7,6,None,None,5,None,None,None,4,3,None,None,None,2,None,4,6,None,None,None,None,4,2,2,None,5,None,6,None,None,None,6,None,6,None,5,None,None,None,5,None,None,7,None,None],[2,None,4,4,2,4,None,None,6,5,None,3,None,None,4,4,3,None,4,None,5,6,6,None,None,None,3,2,None,3,None,4,5,4,None,None,None,None,6,4,None,5,7,6,6,6,None,None,6,5],[3,None,4,None,2,4,5,8,9,None,6,None,None,2,None,None,4,None,6,6,None,None,5,None,5,None,None,3,5,6,6,None,4,5,4,None,None,5,None,4,5,5,None,6,None,None,None,None,6,None],[5,7,None,None,None,3,3,5,None,7,7,6,None,None,3,None,7,7,7,6,None,None,4,None,3,4,None,None,6,7,5,None,3,None,4,None,5,5,5,4,None,5,6,5,None,3,None,5,5,2],[None,None,6,5,5,None,None,5,None,None,None,6,None,3,3,4,6,6,6,5,None,6,None,5,None,3,4,5,8,None,None,4,4,None,4,None,4,None,None,None,6,7,None,None,None,None,None,None,None,None],[None,4,None,None,None,None,None,None,4,4,None,3,None,None,3,None,None,None,3,3,3,4,None,None,None,2,4,None,None,5,None,3,3,None,None,None,None,None,None,2,4,None,None,5,3,1,None,1,2,None]]

#

size=len(task)
answer=[[-1] * size for _ in range(size)]
effect=1
while effect>0:
    effect=0
    for i in range(size):
        for j in range(size):
            effect += nearself((i,j))
            effect += near4((i,j))
            effect += near8((i,j))
            effect += near44((i,j))
    print(effect)
'''
for i in answer:
    print(i)
'''
unknown=0
for i in range(size):
    for j in range(size):
        if answer[i][j]==-1:
            unknown+=1
print(unknown)


import tkinter as tk
def show_board(task, answer):
    size = len(task)
    root = tk.Tk()
    root.title(f"Mosaic Solver Visualization ({size}x{size})")

    # 根据屏幕自适应格子尺寸（30x30 时约 25 像素一格，总宽约 750px）
    cell_size = max(18, min(30, 780 // size))
    canvas_w = cell_size * size
    canvas_h = cell_size * size

    canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="#333333")
    canvas.pack(padx=10, pady=10)

    # 1. 格子背景颜色映射
    bg_colors = {
        -1: "#A9A9A9",  # 未知格：灰色
         0: "#FFFFFF",  # 确定白：纯白
         1: "#1A1A1A"   # 确定黑：深黑
    }

    # 2. 数字文字颜色映射（确保在不同背景上都有极高辨识度）
    text_colors = {
        -1: "#00008B",  # 灰色背景上用深蓝字
         0: "#000000",  # 白色背景上用纯黑字
         1: "#00FFFF"   # 黑色背景上用亮青字（极度醒目！）
    }

    font_size = max(8, int(cell_size * 0.45))
    font_style = ("Consolas", font_size, "bold")

    # 绘制棋盘
    for r in range(size):
        for c in range(size):
            x1 = c * cell_size
            y1 = r * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size

            state = answer[r][c]
            bg = bg_colors.get(state, "#A9A9A9")

            # 绘制方块与细网格边框
            canvas.create_rectangle(x1, y1, x2, y2, fill=bg, outline="#666666", width=1)

            # 绘制数字
            clue = task[r][c]
            if clue is not None:
                fg = text_colors.get(state, "#000000")
                canvas.create_text(
                    x1 + cell_size / 2, 
                    y1 + cell_size / 2, 
                    text=str(clue), 
                    fill=fg, 
                    font=font_style
                )

    root.mainloop()

# 启动可视化窗口！
show_board(task, answer)
