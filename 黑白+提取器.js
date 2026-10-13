(function() {
    // 1. 抓取所有棋盘格子
    let cells = Array.from(document.querySelectorAll('div[tabindex="-1"]')).filter(c => 
        c.classList.contains('cell') || c.classList.contains('task-cell')
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

    let firstRow = rowsMap.get(sortedRowTops[0]);
    firstRow.sort((a, b) => a.offsetLeft - b.offsetLeft);
    let sortedColLefts = firstRow.map(c => c.offsetLeft);

    let cell_h = sortedRowTops.length > 1 ? (sortedRowTops[1] - sortedRowTops[0]) : 35;
    let cell_w = sortedColLefts.length > 1 ? (sortedColLefts[1] - sortedColLefts[0]) : 35;

    // 2. 提取基础棋盘状态 (黑1, 白0, 未知-1)
    let grid = [];
    for (let topKey of sortedRowTops) {
        let rowCells = rowsMap.get(topKey);
        rowCells.sort((a, b) => a.offsetLeft - b.offsetLeft);
        let rowData = [];
        for (let c of rowCells) {
            if (c.classList.contains('cell-1')) rowData.push(1);
            else if (c.classList.contains('cell-0')) rowData.push(0);
            else rowData.push(-1);
        }
        grid.push(rowData);
    }

    // 3. 修正后的线索提取（修复作者 h/v 分界线命名反转！）
    let clues = Array.from(document.querySelectorAll('.comparison-clue'));
    let same_pairs = []; // 相等对 (=)
    let diff_pairs = []; // 不等对 (x)

    function findClosestIndex(arr, val) {
        let bestIdx = 0, minDiff = Infinity;
        for (let i = 0; i < arr.length; i++) {
            let diff = Math.abs(arr[i] - val);
            if (diff < minDiff) { minDiff = diff; bestIdx = i; }
        }
        return bestIdx;
    }

    clues.forEach(el => {
        let isEq = el.classList.contains('eqh') || el.classList.contains('eqv') || el.classList.contains('icon-eq');
        
        // 关键修正：
        // eqv / nev = 竖直分界线 -> 分隔左右两格 (Left-Right)！
        // eqh / neh = 水平分界线 -> 分隔上下两格 (Top-Bottom)！
        let isLeftRight = el.classList.contains('eqv') || el.classList.contains('nev');

        let top = el.offsetTop;
        let left = el.offsetLeft;

        if (isLeftRight) {
            // 左右关系：行在中心半高处，列在分界右格首
            let r = findClosestIndex(sortedRowTops, top - cell_h / 2);
            let rightCol = findClosestIndex(sortedColLefts, left);
            let leftCol = rightCol - 1;

            if (0 <= r && r < height && 0 <= leftCol && rightCol < width) {
                let pair = [[r, leftCol], [r, rightCol]];
                if (isEq) same_pairs.push(pair);
                else diff_pairs.push(pair);
            }
        } else {
            // 上下关系：列在中心半宽处，行在分界下格首
            let c = findClosestIndex(sortedColLefts, left - cell_w / 2);
            let bottomRow = findClosestIndex(sortedRowTops, top);
            let topRow = bottomRow - 1;

            if (0 <= c && c < width && 0 <= topRow && bottomRow < height) {
                let pair = [[topRow, c], [bottomRow, c]];
                if (isEq) same_pairs.push(pair);
                else diff_pairs.push(pair);
            }
        }
    });

    console.log(`%c✔ 黑白+ 修正提取成功！宽 ${width} x 高 ${height} | 相等对: ${same_pairs.length}, 不等对: ${diff_pairs.length}`, "color: green; font-weight: bold;");

    let pyCode = `width = ${width}\n` +
                 `height = ${height}\n` +
                 `grid = ${JSON.stringify(grid)}\n` +
                 `same_pairs = ${JSON.stringify(same_pairs).replace(/\[/g, "(").replace(/\]/g, ")")}\n` +
                 `diff_pairs = ${JSON.stringify(diff_pairs).replace(/\[/g, "(").replace(/\]/g, ")")}`;

    copy(pyCode);
    console.log("已复制到剪贴板，快去可视化窗口看对齐效果！");
})();