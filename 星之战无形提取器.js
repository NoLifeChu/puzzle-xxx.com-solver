(function() {
    // 1. 抓取所有棋盘格子 (带 tabindex="-1" 的有效单元格)
    let cells = Array.from(document.querySelectorAll('div[tabindex="-1"]')).filter(c => 
        c.classList.contains('cell') && c.classList.contains('selectable')
    );
    console.log(`检测到 ${cells.length} 个无形星之战格子...`);

    // 2. 物理坐标聚类行和列
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

    // 3. 构建网格：黑墙直接记为 0 (相当于天然打叉)，空格记为 -1
    let grid = [];
    let walls = [];

    for (let r = 0; r < height; r++) {
        let rowCells = rowsMap.get(sortedRowTops[r]);
        rowCells.sort((a, b) => a.offsetLeft - b.offsetLeft);
        let rowData = [];

        for (let c = 0; c < width; c++) {
            let cell = rowCells[c];
            // 带有 wall 类名的即为障碍物
            let isWall = cell.classList.contains('wall');
            if (isWall) {
                rowData.push(0); // 黑色障碍墙预设为 0 (禁入)
                walls.push([r, c]);
            } else {
                rowData.push(-1); // 可填白格
            }
        }
        grid.push(rowData);
    }

    // 4. 精准提取星星数量与题目编号
    let stars = 2; // 默认 2 星
    let puzzleId = "";
    let infoEl = document.querySelector('.puzzleInfo');
    if (infoEl) {
        let text = infoEl.innerText;
        let starMatch = text.match(/(\d+)\s*★/) || text.match(/(\d+)\s*star/i);
        if (starMatch) stars = parseInt(starMatch[1]);
        let idMatch = text.match(/题号:\s*([0-9,]+)/) || text.match(/id:\s*([0-9,]+)/i);
        if (idMatch) puzzleId = idMatch[1];
    }

    console.log(`%c✔ 无形星之战抓取成功！边长: ${width}x${height} | 每行/列 ${stars}★ 颗星 | 障碍黑墙: ${walls.length} 个`, "color: green; font-weight: bold;");

    // 5. 格式化并复制到剪贴板
    let pyCode = `# 无形的星之战 题号: ${puzzleId}\n` +
                 `size = ${width}\n` +
                 `stars = ${stars}\n` +
                 `grid = ${JSON.stringify(grid)}\n` +
                 `walls = ${JSON.stringify(walls).replace(/\[/g, "(").replace(/\]/g, ")")}`;

    copy(pyCode);
    console.log("已复制 Python 数据到系统剪贴板！可以直接粘贴使用。");
})();