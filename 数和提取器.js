(function() {
    let cells = Array.from(document.querySelectorAll('.cell.selectable'));
    console.log(`检测到 ${cells.length} 个数和格子...`);

    // 1. 自动根据像素坐标把格子聚类成二维矩阵 (防止 DOM 错位)
    cells.sort((a, b) => a.offsetTop - b.offsetTop || a.offsetLeft - b.offsetLeft);

    let rowsMap = new Map();
    cells.forEach(c => {
        let top = c.offsetTop;
        let foundKey = null;
        for (let k of rowsMap.keys()) {
            if (Math.abs(k - top) < 5) {
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

    console.log(`%c✔ 尺寸检测成功: 高 ${height} x 宽 ${width} (总计 ${height * width} 格)`, "color: green; font-weight: bold;");

    // 2. 遍历提取每个格子的真实身份
    let grid = [];
    for (let topKey of sortedRowTops) {
        let rowCells = rowsMap.get(topKey);
        rowCells.sort((a, b) => a.offsetLeft - b.offsetLeft);

        let rowData = [];
        for (let c of rowCells) {
            let isWall = c.classList.contains('wall');
            let isTask = c.classList.contains('task');

            if (isTask) {
                // 提取垂直向下 (v) 和 水平向右 (h) 线索
                let vEl = c.querySelector('.task-vertical');
                let hEl = c.querySelector('.task-horizontal');
                let v = vEl ? parseInt(vEl.innerText.trim()) : 0;
                let h = hEl ? parseInt(hEl.innerText.trim()) : 0;
                rowData.push([isNaN(v) ? 0 : v, isNaN(h) ? 0 : h]);
            } else if (isWall) {
                // 纯黑墙
                rowData.push(null);
            } else {
                // 白格（可填格）：初始为 0
                let numEl = c.querySelector('.number');
                let num = numEl ? parseInt(numEl.innerText.trim()) : 0;
                rowData.push(isNaN(num) ? 0 : num);
            }
        }
        grid.push(rowData);
    }

    // 3. 复制到剪贴板
    let pyCode = `height = ${height}\nwidth = ${width}\ngrid = ${JSON.stringify(grid).replace(/null/g, "None")}`;
    copy(pyCode);

    console.log("%c✔ 数和盘面全量提取成功！已复制到系统剪贴板！", "color: green; font-size: 14px; font-weight: bold;");
})();