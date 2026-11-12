(function() {
    let dots = Array.from(document.querySelectorAll('.loop-dot'));
    if (!dots.length) {
        console.error("未找到 .loop-dot 元素！");
        return;
    }

    // 1. 辅助函数：从 style 或计算样式中精确读取浮点像素
    function getPx(el, prop) {
        let val = el.style[prop];
        if (val && val.includes('px')) return parseFloat(val);
        return el.getBoundingClientRect()[prop === 'top' ? 'top' : 'left'];
    }

    // 2. 聚类提取所有唯一的 Y 坐标（行）与 X 坐标（列），5px 容差防抖
    function cluster(values) {
        values.sort((a, b) => a - b);
        let res = [];
        values.forEach(v => {
            if (!res.some(existing => Math.abs(existing - v) < 5)) {
                res.push(v);
            }
        });
        return res.sort((a, b) => a - b);
    }

    let allY = dots.map(d => getPx(d, 'top'));
    let allX = dots.map(d => getPx(d, 'left'));

    let uniqueY = cluster(allY);
    let uniqueX = cluster(allX);
    let size = uniqueY.length;

    function getIndex(val, arr) {
        let bestIdx = 0, minDiff = 999999;
        for (let i = 0; i < arr.length; i++) {
            let diff = Math.abs(val - arr[i]);
            if (diff < minDiff) {
                minDiff = diff;
                bestIdx = i;
            }
        }
        return bestIdx;
    }

    // 3. 直接定位白圈与黑圈的真实物理 (r, c)
    let white_circles = [];
    let black_circles = [];

    dots.forEach(el => {
        let isWhite = el.classList.contains('dot-white');
        let isBlack = el.classList.contains('dot-black');

        if (isWhite || isBlack) {
            let y_px = getPx(el, 'top');
            let x_px = getPx(el, 'left');

            let r = getIndex(y_px, uniqueY);
            let c = getIndex(x_px, uniqueX);

            let span = el.querySelector('span') || el;
            let txt = span ? span.innerText.trim() : "";
            let num = (txt !== "" && !isNaN(txt)) ? parseInt(txt) : 0;

            if (isWhite) {
                white_circles.push(`(${r}, ${c}, ${num})`);
            } else {
                black_circles.push(`(${r}, ${c}, ${num})`);
            }
        }
    });

    // 4. 组装 Python 代码并复制（无 grid，只保留三件套）
    let pyCode = `size = ${size}\n` +
                 `white_circles = [${white_circles.join(', ')}]\n` +
                 `black_circles = [${black_circles.join(', ')}]`;

    copy(pyCode);

    console.log(`%c✔ 信号旗数据提取成功！尺寸: ${size}x${size}`, "color: green; font-size: 14px; font-weight: bold;");
    console.log(`共提取到 ${white_circles.length} 个白圈，${black_circles.length} 个黑圈（已完美对齐列坐标）。`);
})();