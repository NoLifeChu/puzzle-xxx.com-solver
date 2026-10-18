(function() {
    // 1. 抓取所有棋盘格子并聚类网格 (正方形 N x N)
    let cells = Array.from(document.querySelectorAll('div[tabindex="-1"]')).filter(c => 
        c.classList.contains('cell') && c.classList.contains('selectable')
    );
    console.log(`检测到 ${cells.length} 个温度计格子...`);

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
    let size = sortedRowTops.length; // 正方形尺寸 N

    let gridElements = [];
    for (let topKey of sortedRowTops) {
        let rowCells = rowsMap.get(topKey);
        rowCells.sort((a, b) => a.offsetLeft - b.offsetLeft);
        gridElements.push(rowCells);
    }

    // 2. 真实旋转朝向矩阵 (UP: [-1,0], RIGHT: [0,1], DOWN: [1,0], LEFT: [0,-1])
    const UP = [-1, 0], RIGHT = [0, 1], DOWN = [1, 0], LEFT = [0, -1];

    function getPorts(el) {
        let r = 0;
        if (el.classList.contains('r1')) r = 1;
        else if (el.classList.contains('r2')) r = 2;
        else if (el.classList.contains('r3')) r = 3;

        if (el.classList.contains('start') || el.classList.contains('end')) {
            if (r === 0) return [UP];
            if (r === 1) return [RIGHT];
            if (r === 2) return [DOWN];
            if (r === 3) return [LEFT];
        } else if (el.classList.contains('straight')) {
            if (r === 0 || r === 2) return [UP, DOWN];
            if (r === 1 || r === 3) return [LEFT, RIGHT];
        } else if (el.classList.contains('curve')) {
            if (r === 0) return [UP, RIGHT];
            if (r === 1) return [RIGHT, DOWN];
            if (r === 2) return [DOWN, LEFT];
            if (r === 3) return [LEFT, UP];
        }
        return [];
    }

    // 3. 追踪温度计导管 (从水银泡一路顺流至封口)
    let thermometers = [];
    let visited = Array.from({length: size}, () => Array(size).fill(false));

    for (let r = 0; r < size; r++) {
        for (let c = 0; c < size; c++) {
            let el = gridElements[r][c];
            if (el.classList.contains('start') && !visited[r][c]) {
                let path = [[r, c]];
                visited[r][c] = true;

                let curr_r = r, curr_c = c;
                let ports = getPorts(el);
                if (ports.length === 0) continue;

                let prev_r = curr_r, prev_c = curr_c;
                curr_r += ports[0][0];
                curr_c += ports[0][1];

                while (true) {
                    if (curr_r < 0 || curr_r >= size || curr_c < 0 || curr_c >= size) break;
                    let nextEl = gridElements[curr_r][curr_c];
                    if (!nextEl) break;

                    path.push([curr_r, curr_c]);
                    visited[curr_r][curr_c] = true;

                    if (nextEl.classList.contains('end')) break;

                    let nextPorts = getPorts(nextEl);
                    let forwardPort = nextPorts.find(p => (curr_r + p[0] !== prev_r) || (curr_c + p[1] !== prev_c));
                    if (!forwardPort) break;

                    prev_r = curr_r;
                    prev_c = curr_c;
                    curr_r += forwardPort[0];
                    curr_c += forwardPort[1];
                }
                thermometers.push(path);
            }
        }
    }

    // 4. 精准抓取行列目标数字 (按 .cell.task.h 与 .cell.task.v)
    let rowTaskEls = Array.from(document.querySelectorAll('.cell.task.h, .task.h'));
    rowTaskEls.sort((a, b) => a.offsetTop - b.offsetTop);
    let row_tasks = rowTaskEls.map(el => parseInt(el.innerText.trim())).filter(n => !isNaN(n)).slice(0, size);

    let colTaskEls = Array.from(document.querySelectorAll('.cell.task.v, .task.v'));
    colTaskEls.sort((a, b) => a.offsetLeft - b.offsetLeft);
    let col_tasks = colTaskEls.map(el => parseInt(el.innerText.trim())).filter(n => !isNaN(n)).slice(0, size);

    console.log(`%c✔ 温度计识别成功！正方形尺寸: ${size}x${size} | 共 ${thermometers.length} 根导管`, "color: green; font-weight: bold;");

    // 5. 格式化输出 Python 代码 (统一为 size)
    let pyCode = `size = ${size}\n` +
                 `row_tasks = ${JSON.stringify(row_tasks)}\n` +
                 `col_tasks = ${JSON.stringify(col_tasks)}\n` +
                 `thermometers = ${JSON.stringify(thermometers).replace(/\[/g, "(").replace(/\]/g, ")")}`;

    copy(pyCode);
    console.log("已复制 Python 格式数据到系统剪贴板！");
})();