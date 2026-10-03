(function() {
    function getClues(selector, sortProp) {
        let els = Array.from(document.querySelectorAll(selector));
        els.sort((a, b) => a[sortProp] - b[sortProp]);
        return els.map(el => {
            let txt = el.innerText.trim();
            return (txt !== "" && !isNaN(txt)) ? parseInt(txt) : 0;
        });
    }

    let topClues    = getClues('.task-top', 'offsetLeft');
    let bottomClues = getClues('.task-bottom', 'offsetLeft');
    let leftClues   = getClues('.task-left', 'offsetTop');
    let rightClues  = getClues('.task-right', 'offsetTop');

    let size = topClues.length;

    // 1. 打包成 (起点, 终点) 的复合元组列表
    let row_task = [];
    let col_task = [];
    for (let i = 0; i < size; i++) {
        row_task.push([leftClues[i], rightClues[i]]);
        col_task.push([topClues[i], bottomClues[i]]);
    }

    // 2. 抓取盘面已固定的数字
    let gridCells = Array.from(document.querySelectorAll('.cell.selectable'));
    gridCells.sort((a, b) => {
        let topDiff = a.offsetTop - b.offsetTop;
        if (Math.abs(topDiff) > 5) return topDiff;
        return a.offsetLeft - b.offsetLeft;
    });

    let grid = [];
    for (let r = 0; r < size; r++) {
        let row = [];
        for (let c = 0; c < size; c++) {
            let cell = gridCells[r * size + c];
            let numEl = cell ? cell.querySelector('.number') : null;
            let txt = numEl ? numEl.innerText.trim() : "";
            row.push(txt !== "" && !isNaN(txt) ? parseInt(txt) : 0);
        }
        grid.push(row);
    }

    // 3. 复制 Python 代码（统一规范，size 放在末尾通过 len 自动获取）
    let pyCode = `row_task = ${JSON.stringify(row_task).replace(/\[/g, "(").replace(/\]/g, ")")}\n` +
                 `col_task = ${JSON.stringify(col_task).replace(/\[/g, "(").replace(/\]/g, ")")}\n` +
                 `grid = ${JSON.stringify(grid)}\n` +
                 `size = len(row_task)`+`\n`;

    copy(pyCode);

    console.log(`%c✔ 高楼数据提取成功！(尺寸 ${size}x${size}) 已格式化为复合元组！`, "color: green; font-size: 14px; font-weight: bold;");
    console.log("row_task 前3行预览:", row_task.slice(0, 3));
    console.log("col_task 前3列预览:", col_task.slice(0, 3));
})();