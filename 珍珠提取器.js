(function() {
    // 1. 抓取所有珍珠/黑点元素
    let dots = Array.from(document.querySelectorAll('.loop-dot'));
    
    // 2. 核心大招：提取全盘所有不同的 left（列像素）和 top（行像素），并从小到大排序
    // 用 5px 容差聚类出全盘真实的全部列坐标（0 到 size-1）
    function clusterCoords(prop) {
        let sorted = Array.from(new Set(dots.map(d => d[prop]))).sort((a, b) => a - b);
        let clustered = [];
        sorted.forEach(val => {
            if (!clustered.length || val - clustered[clustered.length - 1] > 8) {
                clustered.push(val);
            }
        });
        return clustered;
    }

    let all_rows = clusterCoords('offsetTop');
    let all_cols = clusterCoords('offsetLeft');
    let size = all_rows.length;

    function getIndex(val, clusters) {
        for (let i = 0; i < clusters.length; i++) {
            if (Math.abs(val - clusters[i]) <= 8) return i;
        }
        return 0;
    }

    // 3. 提取珍珠：物理像素精准映射为网格真实行列！
    let white_pearls = [];
    let black_pearls = [];

    dots.forEach(el => {
        let r = getIndex(el.offsetTop, all_rows);
        let c = getIndex(el.offsetLeft, all_cols); // 真实列号 c 绝不会再缩回 0, 1, 2！

        if (el.classList.contains('dot-white')) {
            white_pearls.push(`(${r}, ${c})`);
        } else if (el.classList.contains('dot-black')) {
            black_pearls.push(`(${r}, ${c})`);
        }
    });

    // 4. 复制真实数据
    let pyCode = `size = ${size}\n` +
                 `white_pearls = [${white_pearls.join(', ')}]\n` +
                 `black_pearls = [${black_pearls.join(', ')}]`;

    copy(pyCode);
    console.log(`%c✔ 真实坐标提取成功！尺寸 ${size}x${size}，白珠 ${white_pearls.length}，黑珠 ${black_pearls.length}`, "color: green; font-size: 14px; font-weight: bold;");
})();