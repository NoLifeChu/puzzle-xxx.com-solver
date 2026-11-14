(function() {
    let cells = Array.from(document.querySelectorAll('.cell.selectable'));
    if (!cells.length) {
        console.error("未找到棋盘格子！");
        return;
    }

    // 1. 获取棋盘尺寸 N (N x N 个格子)
    let size = Math.round(Math.sqrt(cells.length));

    // 2. 物理坐标与步长采样 (使用 getBoundingClientRect 保证绝对精准)
    cells.sort((a, b) => a.offsetTop - b.offsetTop || a.offsetLeft - b.offsetLeft);
    let c0 = cells[0].getBoundingClientRect();
    let c1 = cells[1].getBoundingClientRect();
    let step = c1.left - c0.left;
    let originX = c0.left;
    let originY = c0.top;

    // 3. 提取所有数字线索并映射到晶格点 (r, c)，其中 0 <= r, c <= size
    let tasks = Array.from(document.querySelectorAll('.task'));
    let cluesList = [];

    tasks.forEach(t => {
        let rect = t.getBoundingClientRect();
        let cx = rect.left + rect.width / 2;
        let cy = rect.top + rect.height / 2;

        let c = Math.round((cx - originX) / step);
        let r = Math.round((cy - originY) / step);

        let txt = t.innerText.trim();
        if (txt !== "" && !isNaN(txt)) {
            let num = parseInt(txt);
            cluesList.push(`(${r}, ${c}): ${num}`);
        }
    });

    // 4. 组装 Python 代码并复制
    let pyCode = `size = ${size}\n` +
                 `clues = {`+ cluesList.join(', ') + `\n}`;

    copy(pyCode);

    console.log(`%c✔ 划斜线数据提取成功！尺寸: ${size}x${size}`, "color: green; font-size: 14px; font-weight: bold;");
    console.log(`成功提取 ${cluesList.length} 个顶点线索，已复制到剪贴板！`);
})();