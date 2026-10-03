(function() {
    // 1. 抓取行目标（右侧数字），按垂直高度 top 从上到下排序
    let rowEls = Array.from(document.querySelectorAll('.side-counter.task, .side-counter'));
    rowEls.sort((a, b) => a.offsetTop - b.offsetTop);
    let rowTargets = rowEls.map(el => {
        let span = el.querySelector('.sc1') || el.querySelector('.sc2') || el;
        return parseInt(span.innerText.trim());
    }).filter(n => !isNaN(n));

    // 2. 抓取列目标（底部数字），按水平位置 left 从左到右排序
    let colEls = Array.from(document.querySelectorAll('.bottom-counter.task, .bottom-counter, .top-counters .task'));
    colEls.sort((a, b) => a.offsetLeft - b.offsetLeft);
    let colTargets = colEls.map(el => {
        let span = el.querySelector('.sc1') || el.querySelector('.sc2') || el;
        return parseInt(span.innerText.trim());
    }).filter(n => !isNaN(n));

    console.log("行目标 (Rows):", rowTargets);
    console.log("列目标 (Cols):", colTargets);

    // 3. 自动生成 Python 变量并直接复制到系统剪贴板
    let pyCode = `row_task = ${JSON.stringify(rowTargets)}\ncol_task = ${JSON.stringify(colTargets)}`;
    copy(pyCode);

    console.log(`%c✔ 提取成功！(${rowTargets.length}x${colTargets.length}) 已复制到剪贴板！`, "color: green; font-size: 14px; font-weight: bold;");
})();