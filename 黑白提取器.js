(function() {
    // 1. 抓取所有带有 tabindex="-1" 的棋盘格子（避开外围 a-z 和 1-40 的坐标轴标签）
    let cells = Array.from(document.querySelectorAll('div[tabindex="-1"]')).filter(c => 
        c.classList.contains('cell') || c.classList.contains('task-cell')
    );
    console.log(`检测到 ${cells.length} 个黑白格子...`);

    // 2. 物理坐标容差聚类：自动按垂直高度 top 分行
    cells.sort((a, b) => a.offsetTop - b.offsetTop || a.offsetLeft - b.offsetLeft);

    let rowsMap = new Map();
    cells.forEach(c => {
        let top = c.offsetTop;
        let foundKey = null;
        for (let k of rowsMap.keys()) {
            if (Math.abs(k - top) < 5) { // 5px 容差聚类同一行
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

    console.log(`%c✔ 尺寸自适应检测成功: 宽 ${width} x 高 ${height} (总计 ${height * width} 格)`, "color: green; font-weight: bold;");

    // 3. 提取矩阵数值：黑=1, 白=0, 未知=-1
    let grid = [];
    for (let topKey of sortedRowTops) {
        let rowCells = rowsMap.get(topKey);
        rowCells.sort((a, b) => a.offsetLeft - b.offsetLeft); // 每行按 left 从左到右排

        let rowData = [];
        for (let c of rowCells) {
            if (c.classList.contains('cell-1')) {
                rowData.push(1);  // 黑子
            } else if (c.classList.contains('cell-0')) {
                rowData.push(0);  // 白子
            } else {
                rowData.push(-1); // 未填未知格
            }
        }
        grid.push(rowData);
    }

    // 4. 生成 Python 规范代码并复制到剪贴板
    let pyCode = `width = ${width}\n` +
                 `height = ${height}\n` +
                 `grid = ${JSON.stringify(grid)}`;

    copy(pyCode);
    console.log("%c✔ 黑白数据全量提取成功！已复制到系统剪贴板！", "color: green; font-size: 14px; font-weight: bold;");
    console.log("前 2 行数据预览:", grid.slice(0, 2));
})();