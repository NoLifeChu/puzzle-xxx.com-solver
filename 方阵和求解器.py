from itertools import product

def main():
    size = len(row_task)
    
    # 1. 生成四库全书：存纯粹的 0/1 元组，根据加权和归类
    # 比如 biglist[14] 存所有加权和等于 14 的 (0, 1, 0, ...) 序列
    biglist = {}
    weights = [i + 1 for i in range(size)] # [1, 2, 3, ..., size]
    
    for bits in product([0, 1], repeat=size):
        # 计算当前 01 序列的加权和
        current_sum = sum(b * w for b, w in zip(bits, weights))
        if current_sum not in biglist:
            biglist[current_sum] = []
        biglist[current_sum].append(bits)

    answer = [[-1] * size for _ in range(size)]
    effect = 1
    
    while effect > 0:
        effect = 0
        
        # --- 行检查 ---
        for i in range(size):
            target = row_task[i]
            # 取出所有总和符合要求的备选方案
            possibility = biglist.get(target, [])
            
            # 用列表推导式过滤，彻底告别一边循环一边 remove 的 Bug！
            for j in range(size):
                if answer[i][j] == 0:
                    possibility = [p for p in possibility if p[j] == 0]
                elif answer[i][j] == 1:
                    possibility = [p for p in possibility if p[j] == 1]
            
            if not possibility:
                continue # 没有备选方案说明可能发生矛盾
                
            # 统计这一行在每一个未知格上的共识
            for j in range(size):
                if answer[i][j] != -1:
                    continue
                # 取出所有备选方案在第 j 格上的取值集合
                values_at_j = {p[j] for p in possibility}
                if values_at_j == {1}: # 所有解法都必须选它
                    answer[i][j] = 1
                    effect += 1
                elif values_at_j == {0}: # 所有解法都不能选它
                    answer[i][j] = 0
                    effect += 1

        # --- 列检查（和行检查完全镜像，直接复制改几个下标就行！） ---
        for j in range(size):
            target = col_task[j]
            possibility = biglist.get(target, [])
            
            for i in range(size):
                if answer[i][j] == 0:
                    possibility = [p for p in possibility if p[i] == 0]
                elif answer[i][j] == 1:
                    possibility = [p for p in possibility if p[i] == 1]
                    
            if not possibility:
                continue
                
            for i in range(size):
                if answer[i][j] != -1:
                    continue
                values_at_i = {p[i] for p in possibility}
                if values_at_i == {1}:
                    answer[i][j] = 1
                    effect += 1
                elif values_at_i == {0}:
                    answer[i][j] = 0
                    effect += 1

    return answer

#
row_task = [47,72,77,55,39,56,74,57,70,30,44,63]
col_task = [33,67,47,65,61,75,44,67,32,51,52,65]

#


ll = main()
for r in ll:
    print(r)