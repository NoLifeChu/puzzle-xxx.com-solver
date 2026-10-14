(function() {
    // 1. 抓取所有棋盘格子并聚类行、列物理坐标
    let cells = Array.from(document.querySelectorAll('div[tabindex="-1"]')).filter(c => 
        c.classList.contains('cell') && c.classList.contains('selectable')
    );
    console.log(`检测到 ${cells.length} 个星之战格子...`);

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

    let gridElements = [];
    for (let topKey of sortedRowTops) {
        let rowCells = rowsMap.get(topKey);
        rowCells.sort((a, b) => a.offsetLeft - b.offsetLeft);
        gridElements.push(rowCells);
    }

    // 2. 提取颜色类名和黑边障碍
    function getColor(el) {
        for (let cls of el.classList) {
            if (cls.startsWith('color-')) return cls;
        }
        return '';
    }

    function hasBorderRight(el) { return el.classList.contains('br'); }
    function hasBorderLeft(el) { return el.classList.contains('bl'); }
    function hasBorderBottom(el) { return el.classList.contains('bb'); }
    function hasBorderTop(el) { return el.classList.contains('bt'); }

    // 3. 泛洪算法 (BFS) 严格划分每个不规则区域
    let regionMatrix = Array.from({length: height}, () => Array(width).fill(-1));
    let currentRegionId = 0;

    for (let r = 0; r < height; r++) {
        for (let c = 0; c < width; c++) {
            if (regionMatrix[r][c] !== -1) continue;

            let queue = [[r, c]];
            let targetColor = getColor(gridElements[r][c]);
            regionMatrix[r][c] = currentRegionId;

            while (queue.length > 0) {
                let [cr, cc] = queue.shift();
                let currEl = gridElements[cr][cc];

                // 向下扩展
                if (cr + 1 < height && regionMatrix[cr + 1][cc] === -1) {
                    let nextEl = gridElements[cr + 1][cc];
                    if (!hasBorderBottom(currEl) && !hasBorderTop(nextEl) && getColor(nextEl) === targetColor) {
                        regionMatrix[cr + 1][cc] = currentRegionId;
                        queue.push([cr + 1, cc]);
                    }
                }
                // 向上扩展
                if (cr - 1 >= 0 && regionMatrix[cr - 1][cc] === -1) {
                    let nextEl = gridElements[cr - 1][cc];
                    if (!hasBorderTop(currEl) && !hasBorderBottom(nextEl) && getColor(nextEl) === targetColor) {
                        regionMatrix[cr - 1][cc] = currentRegionId;
                        queue.push([cr - 1, cc]);
                    }
                }
                // 向右扩展
                if (cc + 1 < width && regionMatrix[cr][cc + 1] === -1) {
                    let nextEl = gridElements[cr][cc + 1];
                    if (!hasBorderRight(currEl) && !hasBorderLeft(nextEl) && getColor(nextEl) === targetColor) {
                        regionMatrix[cr][cc + 1] = currentRegionId;
                        queue.push([cr, cc + 1]);
                    }
                }
                // 向左扩展
                if (cc - 1 >= 0 && regionMatrix[cr][cc - 1] === -1) {
                    let nextEl = gridElements[cr][cc - 1];
                    if (!hasBorderLeft(currEl) && !hasBorderRight(nextEl) && getColor(nextEl) === targetColor) {
                        regionMatrix[cr][cc - 1] = currentRegionId;
                        queue.push([cr, cc - 1]);
                    }
                }
            }
            currentRegionId++;
        }
    }

    // 4. 自动检测星星数量 (支持 1~4 星)
    // 3. 精准抓取星星数量 (定位 .puzzleInfo 里的 N★)
    let stars = 2; // 默认保底
    let infoEl = document.querySelector('.puzzleInfo');
    if (infoEl) {
        let text = infoEl.innerText.trim();
        // 核心正则：精准匹配紧挨着黑五角星的数字，如 "4★"
        let starMatch = text.match(/(\d+)\s*★/);
        if (starMatch) {
            stars = parseInt(starMatch[1]);
        } else {
            // 英文版兜底正则：匹配 "4 stars" 或 "4 star"
            let engMatch = text.match(/(\d+)\s*star/i);
            if (engMatch) stars = parseInt(engMatch[1]);
        }
    }

    console.log(`%c✔ 星之战识别成功！尺寸: ${width}x${height} | 识别出 ${currentRegionId} 个区域 | 规则: 每行/列/区 ${stars} 颗星`, "color: green; font-weight: bold;");

    let pyCode = `size = ${width}\n` +
                 `stars = ${stars}\n` +
                 `regions = ${JSON.stringify(regionMatrix)}`;

    copy(pyCode);
    console.log("已复制 Python 数据到剪贴板！");
})();