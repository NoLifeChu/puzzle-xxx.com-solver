(function() {
    // 1. 抓取正方形字母网格 (从 .board-back 或 #game 中提取)
    let cells = Array.from(document.querySelectorAll('.board-back .cell, #game .cell.selectable'));
    cells = cells.filter(c => c.getAttribute('data-content') || c.innerText.trim());

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
    let size = sortedRowTops.length;

    let grid = [];
    for (let topKey of sortedRowTops) {
        let rowCells = rowsMap.get(topKey);
        rowCells.sort((a, b) => a.offsetLeft - b.offsetLeft);
        let rowData = rowCells.map(c => {
            let letter = c.getAttribute('data-content') || c.innerText.trim();
            return letter.toUpperCase();
        });
        grid.push(rowData);
    }

    // 2. 抓取待搜寻单词列表 (从 .word-list 中提取)
    let wordEls = Array.from(document.querySelectorAll('.word-list div'));
    let target = {};
    wordEls.forEach(el => {
        let w = el.innerText.trim().toUpperCase();
        if (w) target[w] = [];
    });

    console.log(`%c✔ 单词寻找抓取成功！尺寸: ${size}x${size} | 单词数量: ${Object.keys(target).length} 个`, "color: green; font-weight: bold;");
    console.log("前 2 行字母:", grid.slice(0, 2));
    console.log("单词列表:", Object.keys(target));

    // 3. 复制 Python 规范代码
    let pyCode = `size = ${size}\n` +
                 `grid = ${JSON.stringify(grid)}\n` +
                 `target = ${JSON.stringify(target)}`;

    copy(pyCode);
    console.log("已复制 Python 数据到系统剪贴板！可以直接粘贴使用。");
})();