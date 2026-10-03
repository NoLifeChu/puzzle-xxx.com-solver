(function() {
    // 1. 抓取所有可交互的棋盘格子
    let cells = Array.from(document.querySelectorAll('.cell.selectable'));
    console.log(`检测到 ${cells.length} 个单元格...`);

    // 2. 按照物理像素坐标严格排序：先排 top（行），再排 left（列）
    // 这样哪怕 DOM 顺序乱了，也能 100% 还原成人类看到的 30x30 视角
    cells.sort((a, b) => {
        let topA = a.offsetTop, topB = b.offsetTop;
        if (Math.abs(topA - topB) > 5) {
            return topA - topB; // 行距大于5像素算不同行
        }
        return a.offsetLeft - b.offsetLeft; // 同一行按列排
    });

    // 3. 自动计算网格尺寸（比如 900 开根号得到 30）
    let size = Math.round(Math.sqrt(cells.length));
    let matrix = [];

    for (let r = 0; r < size; r++) {
        let row = [];
        for (let c = 0; c < size; c++) {
            let cell = cells[r * size + c];
            let numEl = cell.querySelector('.number');
            let txt = numEl ? numEl.innerText.trim() : cell.innerText.trim();
            // 有数字则存为整数，空则存为 None
            row.push(txt !== "" && !isNaN(txt) ? parseInt(txt) : null);
        }
        matrix.push(row);
    }

    // 4. 转换成标准的 Python 列表语法并写入剪贴板
    let pyCode = JSON.stringify(matrix).replace(/null/g, "None");
    copy(pyCode);
    
    console.log(`%c✔ 成功提取 ${size}x${size} 矩阵！`, "color: green; font-size: 14px; font-weight: bold;");
    console.log("Python 列表已自动复制到系统剪贴板，直接在 Python 文件中 Ctrl+V 即可！");
    console.log("前2行预览：", matrix.slice(0, 2));
})();