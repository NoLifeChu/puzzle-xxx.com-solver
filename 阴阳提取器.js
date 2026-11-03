(function() {
    // 1. 抓取所有棋盘格子 (包含已给黑白子与空位)
    let cells = Array.from(document.querySelectorAll('.task-cell, .cell.selectable'));
    if (!cells.length) {
        cells = Array.from(document.querySelectorAll('.cell'));
    }
    
    // 2. 物理坐标排序 (先按 top 聚类，再按 left 排序)
    cells.sort((a, b) => {
        let topDiff = a.offsetTop - b.offsetTop;
        if (Math.abs(topDiff) > 5) return topDiff;
        return a.offsetLeft - b.offsetLeft;
    });

    let total = cells.length;
    let size = Math.round(Math.sqrt(total));

    // 3. 构造 2D 矩阵 (0: 白子, 1: 黑子, None: 空白待填)
    let grid = [];
    for (let r = 0; r < size; r++) {
        let row = [];
        for (let c = 0; c < size; c++) {
            let el = cells[r * size + c];
            if (el.classList.contains('cell-0')) {
                row.push(0); // 白子
            } else if (el.classList.contains('cell-1')) {
                row.push(1); // 黑子
            } else {
                row.push(null); // 空白
            }
        }
        grid.push(row);
    }

    // 4. 组装 Python 格式并复制到剪贴板
    let pyCode = `size = ${size}\n` +
                 `grid = ${JSON.stringify(grid).replace(/null/g, "-1")}`;

    copy(pyCode);

    console.log(`%c✔ 阴阳数据提取成功！尺寸: ${size}x${size}`, "color: green; font-size: 14px; font-weight: bold;");
    console.log("前2行预览:", grid.slice(0, 2));
    console.log("数据已自动复制到剪贴板，直接在 Python 里 Ctrl+V！");
})();