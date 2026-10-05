# 谜题求解器

针对 [puzzle-***.com](https://cn.puzzle-nonograms.com/) 系列逻辑解谜网站的专用轻量级求解与提取工具集，目前不定期开发中。

## 🛠️ 使用方法

常规尺寸谜题：
1. 打开对应网站的页面，按 `F12` 打开控制台（Console）；
2. 复制对应的 `*提取器.js` 代码粘贴并回车，数据会自动复制到剪贴板；
3. 将数据粘贴进 `*求解器.py` ，替换掉两个#之间的内容并运行，即可获得完整解答！

每日/周/月挑战：（早期求解器暂未配置自动抓取器）
1. 在`*求解器.py`中将抓取代码的网址替换成对应网址并运行，即可自动抓取谜题并给出完整解答！


## 🎯 已收录谜题

1. 马赛克 2026/10/2
2. 扫雷 2026/10/3
3. 方阵和 2026/10/3
4. 高楼 2026/10/3
5. 数和 2026/10/5

## 🗺️ 后续计划
1. [ ] 实现更多谜题的求解器；
2. [x] 实现自动抓取网页谜题，优化控制台——输入抓取代码——粘贴到求解器的步骤；
3. [ ] 统一各个求解器的规范，如输出信息、可视化页面等。

## 🔵 其他
1. 本仓库纯属自娱自乐，你（若真的有人来看）可能会发现各种离谱内容；
2. 求解器目前只写到恰能求解网站的每日/每周/每月挑战的水平，可能无法完全求解更高难度的谜题；
3. 前端 DOM 数据提取器（.js）由 AI 辅助逆向并生成。

# Puzzle Solver

A lightweight toolkit for solving and extracting logic puzzles specifically designed for the [puzzle-***.com](https://www.puzzle-nonograms.com/) series of logic puzzle websites. Currently under development on an irregular basis.

## 🛠️ How to Use

Regular-Size Puzzles:
1. Open the page of the corresponding website and press `F12` to open the console;
2. Copy the corresponding `*提取器.js` code, paste it, and press Enter. The data will be automatically copied to the clipboard;
3. Paste the data into `*求解器.py`, replace the content between the two # symbols, and run the program to get the complete solution!

Daily/Weekly/Monthly Challenges: (Early solvers do not yet have an automatic crawler configured)

1. In `*求解器.py`, replace the URL of the crawling code with the corresponding URL and run the program. The program will automatically crawl the puzzle and provide a complete solution!

## 🎯 Included Puzzles

1. mosaic
2. minesweeper
3. kakurasu
4. skyscrapers
5. kakuro

## 🗺️ Pie in the Sky
1. [ ] Implement more puzzle solvers;
2. [x] Implement automatic scraping of web page puzzles, optimizing the console input—entering scraping code—pasting to the solver steps;
3. [ ] Standardize the specifications of various solvers, such as output information and visualization pages.

## 🔵 Notes
1. This repository is purely for my own amusement; you (if anyone actually visits) might find all sorts of outrageous content;
2. The solver is currently only capable of solving the daily/weekly/monthly challenges on the website, and may not be able to fully solve puzzles of higher difficulty.
3. DOM extraction scripts assisted by AI.
