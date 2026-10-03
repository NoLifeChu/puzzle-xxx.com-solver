from itertools import permutations

def view_count(a):
    view=0
    highest=0
    for i in a:
        if i>highest:
            view+=1
            highest=i
    return view

def delete_candidates(): #删除候选数；虽然每次都完整删较复杂，但size=9下无所谓
    for i in range(size):
        for j in range(size):
            if grid[i][j]!=0:
                candidates[i][j]=[]
                for k in range(size):
                    candidates[k][j]=[a for a in candidates[k][j] if a!=grid[i][j]]
                for k in range(size):
                    candidates[i][k]=[a for a in candidates[i][k] if a!=grid[i][j]]

#
row_task = ((0,4),(2,0),(0,4),(4,4),(4,0),(5,0),(0,1),(3,3),(2,2))
col_task = ((0,3),(0,3),(0,2),(0,3),(5,0),(0,2),(0,3),(0,3),(4,0))
grid = [[0,4,0,0,0,6,0,0,2],[0,0,0,0,3,0,0,0,0],[2,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,1,0,0,0],[0,0,7,0,0,0,3,2,0],[0,0,4,0,0,0,0,0,0],[0,0,0,0,0,0,2,0,3],[0,0,0,0,0,0,4,3,0]]
size = len(row_task)
#

#准备候选数
candidates=[]
for _ in range(size):
    candidates.append([])
    for _ in range(size):
        candidates[-1].append([i for i in range(1,size+1)])
delete_candidates()

#生成四库全书，但9!略大，只储存题目要求的；另外(0,0)不储存
biglist={}
for i in row_task:
    biglist[i]=[]
for i in col_task:
    biglist[i]=[]
for p in permutations(range(1, size + 1)): #p指排列
    sight=(view_count(p),view_count(p[::-1]))
    if sight in biglist:
        biglist[sight].append(p)
    if (sight[0],0) in biglist:
        biglist[(sight[0],0)].append(p)
    if (0,sight[1]) in biglist:
        biglist[(0,sight[1])].append(p)

#正式循环
effect=1
while effect>0:
    effect=0
    #唯一余数
    for i in range(size):
        for j in range(size):
            if len(candidates[i][j])==1:
                effect +=1
                grid[i][j]=candidates[i][j][0]
                delete_candidates()
    #行排除法
    for i in range(size):
        count=[-1]*size
        for j in range(size):
            for k in range(size):
                if k+1 in candidates[i][j]:
                    if count[k]==-1:
                        count[k]=j
                    elif count[k]>=0:
                        count[k]=-99999
        for k in range(size):
            if count[k]>=0:
                effect +=1
                grid[i][count[k]]=k+1
                delete_candidates()
    #列排除法
    for i in range(size):
        count=[-1]*size
        for j in range(size):
            for k in range(size):
                if k+1 in candidates[j][i]:
                    if count[k]==-1:
                        count[k]=j
                    elif count[k]>=0:
                        count[k]=-99999
        for k in range(size):
            if count[k]>=0:
                effect +=1
                grid[count[k]][i]=k+1
                delete_candidates()

    #行高楼
    for i in range(size):
        task=row_task[i]
        possibility = biglist.get(task, [])
        if not possibility:
            continue # 说明是(0,0)
        for j in range(size):
            if grid[i][j]!=0:
                possibility = [a for a in possibility if a[j]==grid[i][j]]
            else:
                possibility = [a for a in possibility if a[j] in candidates[i][j]]
        for j in range(size):
            if grid[i][j]!=0:
                continue
            values_at_j = {p[j] for p in possibility}
            for n in range(1,size+1):
                if (n in candidates[i][j]) and (n not in values_at_j):#只需要统计都不出现，因为“只出现”会淘汰其他候选，从而通过唯一候选出数
                    effect+=1
                    candidates[i][j].remove(n)

    #列高楼
    for i in range(size):
        task=col_task[i]
        possibility = biglist.get(task, [])
        if not possibility:
            continue # 说明是(0,0)
        for j in range(size):
            if grid[j][i]!=0:
                possibility = [a for a in possibility if a[j]==grid[j][i]]
            else:
                possibility = [a for a in possibility if a[j] in candidates[j][i]]
        for j in range(size):
            if grid[j][i]!=0:
                continue
            values_at_j = {p[j] for p in possibility}
            for n in range(1,size+1):
                if (n in candidates[j][i]) and (n not in values_at_j):#只需要统计都不出现，因为“只出现”会淘汰其他候选，从而通过唯一候选出数
                    effect+=1
                    candidates[j][i].remove(n)
    print(effect)
for i in grid:
    print(i)