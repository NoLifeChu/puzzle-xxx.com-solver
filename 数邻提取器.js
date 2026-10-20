(function(){
    // 1. 获取所有绝对定位的格子
    let cells = Array.from(document.querySelectorAll('#game .cell'));
    if (cells.length === 0) {
        cells = Array.from(document.querySelectorAll('#puzzleContainer .cell, [id*="puzzle"] .cell, .board-back ~ div[class*="cell"]'));
    }

    // 2. 提取坐标与数值
    const data = cells.map(c => {
        const span = c.querySelector('span');
        let val = span ? parseInt(span.textContent.trim(), 10) : NaN;
        if (isNaN(val)) {
            const m = c.className.match(/cell(\d+)/);
            if (m) val = parseInt(m[1], 10);
        }
        return {
            top: parseInt(c.style.top, 10),
            left: parseInt(c.style.left, 10),
            val: val
        };
    }).filter(d => !isNaN(d.val) && !isNaN(d.top) && !isNaN(d.left));

    if (data.length === 0) {
        console.error('未找到任何格子，请检查页面是否已加载完毕。');
        return;
    }

    // 3. 根据 top / left 的最小正差值，动态计算每格宽高
    const uniqSort = arr => [...new Set(arr)].sort((a, b) => a - b);
    const tops = uniqSort(data.map(d => d.top));
    const lefts = uniqSort(data.map(d => d.left));

    let cellH = 0, cellW = 0;
    for (let i = 1; i < tops.length; i++) {
        const diff = tops[i] - tops[i-1];
        if (diff > 0) { cellH = diff; break; }
    }
    for (let i = 1; i < lefts.length; i++) {
        const diff = lefts[i] - lefts[i-1];
        if (diff > 0) { cellW = diff; break; }
    }
    if (!cellH || !cellW) {
        const inner = cells[0].querySelector('div');
        if (inner) {
            if (!cellH) cellH = parseInt(inner.style.height, 10) || 22;
            if (!cellW) cellW = parseInt(inner.style.width, 10) || 22;
        }
        if (!cellH) cellH = 22;
        if (!cellW) cellW = 22;
    }

    // 4. 计算行列数并填装二维数组
    const rows = Math.round(Math.max(...data.map(d => d.top)) / cellH) + 1;
    const cols = Math.round(Math.max(...data.map(d => d.left)) / cellW) + 1;

    const grid = Array.from({length: rows}, () => Array(cols).fill(0));
    data.forEach(d => {
        const r = Math.round(d.top / cellH);
        const c = Math.round(d.left / cellW);
        if (r >= 0 && r < rows && c >= 0 && c < cols) grid[r][c] = d.val;
    });

    // 5. 拼成目标字符串（前面所有行放第三行，最后一行放第四行）
    let gridStr;
    const rowStrs = grid.map(row => '[' + row.join(',') + ']');
    if (rowStrs.length <= 1) {
        gridStr = rowStrs.join(',');
    } else {
        gridStr = rowStrs.slice(0, -1).join(',') + ',\n' + rowStrs[rowStrs.length - 1];
    }
    const output = `width=${cols}\nheight=${rows}\ngrid=[${gridStr}]`;

    copy(output)
    console.log("已复制 Python 格式数据到系统剪贴板！");
})();