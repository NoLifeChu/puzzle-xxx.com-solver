(function() {
    // 1. 抓取行要求 (taskLeft)
    let rowContainer = document.querySelector('#taskLeft') || document.querySelector('#taskRight');
    let rowEls = Array.from(rowContainer.querySelectorAll('.cell.task, .task'));
    rowEls.sort((a, b) => a.offsetTop - b.offsetTop);
    let row_task = rowEls.map(el => parseInt(el.innerText.trim())).filter(n => !isNaN(n));

    // 2. 抓取列要求 (taskTop)
    let colContainer = document.querySelector('#taskTop') || document.querySelector('#taskBottom');
    let colEls = Array.from(colContainer.querySelectorAll('.cell.task, .task'));
    colEls.sort((a, b) => a.offsetLeft - b.offsetLeft);
    let col_task = colEls.map(el => parseInt(el.innerText.trim())).filter(n => !isNaN(n));

    let size = row_task.length;

    // 3. 抓取棋盘 (grid 中 1 代表树，0 代表未确定/空地)
    let gridContainer = document.querySelector('.tents-cell-back') || document.querySelector('.board-back');
    let cells = Array.from(gridContainer.querySelectorAll('.cell'));
    cells.sort((a, b) => {
        let topDiff = a.offsetTop - b.offsetTop;
        if (Math.abs(topDiff) > 5) return topDiff;
        return a.offsetLeft - b.offsetLeft;
    });

    let grid = [];
    let tree_coords = [];

    for (let r = 0; r < size; r++) {
        let row = [];
        for (let c = 0; c < size; c++) {
            let cell = cells[r * size + c];
            if (cell && cell.classList.contains('tree-cell')) {
                row.push(1);
                // 格式化为 Python 元组字符串 "(r, c)"
                tree_coords.push(`(${r}, ${c})`);
            } else {
                row.push(0);
            }
        }
        grid.push(row);
    }

    // 4. 组装 Python 代码并复制
    let pyCode = `size = ${size}\n` +
                 `row_task = ${JSON.stringify(row_task)}\n` +
                 `col_task = ${JSON.stringify(col_task)}\n` +
                 `grid = ${JSON.stringify(grid)}\n` +
                 `tree_coords = [${tree_coords.join(', ')}]`;

    copy(pyCode);

    console.log(`%c✔ 帐篷数据提取成功！(尺寸 ${size}x${size})`, "color: green; font-size: 14px; font-weight: bold;");
    console.log("行要求:", row_task);
    console.log("列要求:", col_task);
    console.log(`已将 grid 与 ${tree_coords.length} 个树元组坐标 [(r, c), ...] 复制到剪贴板！`);
})();