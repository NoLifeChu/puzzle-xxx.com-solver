(function() {
    // 1. 抓取所有扫雷网格
    let cells = Array.from(document.querySelectorAll('.cell.selectable'));
    console.log(`检测到 ${cells.length} 个扫雷格子...`);

    // 2. 按物理像素从上到下、从左到右严格排序
    cells.sort((a, b) => {
        let topA = a.offsetTop, topB = b.offsetTop;
        if (Math.abs(topA - topB) > 5) {
            return topA - topB; // 行距差大于5px算不同行
        }
        return a.offsetLeft - b.offsetLeft; // 同一行按列排
    });

    // 3. 自动计算网格尺寸（比如 625 个格子算出 25x25）
    let size = Math.round(Math.sqrt(cells.length));
    let matrix = [];

    for (let r = 0; r < size; r++) {
        let row = [];
        for (let c = 0; c < size; c++) {
            let cell = cells[r * size + c];
            let numEl = cell ? cell.querySelector('.number') : null;
            let txt = numEl ? numEl.innerText.trim() : (cell ? cell.innerText.trim() : "");
            // 有数字存数字，无数字存 None
            row.push(txt !== "" && !isNaN(txt) ? parseInt(txt) : null);
        }
        matrix.push(row);
    }

    // 4. 格式化并复制到剪贴板
    let pyCode = `task = ${JSON.stringify(matrix).replace(/null/g, "None")}`;
    copy(pyCode);

    console.log(`%c✔ 扫雷 ${size}x${size} 数据提取成功！`, "color: green; font-size: 14px; font-weight: bold;");
    console.log("Python 矩阵变量已自动复制到系统剪贴板，直接在编辑器里 Ctrl+V！");
})();