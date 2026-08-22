# PaperLister 文献题录管家 v0.1.0

知网 + NCBI/PubMed + Google Scholar 多源文献**题录**检索 → 一键入库 Zotero 的 Windows 便携工具。
（v0.1 = 题录版：不做 PDF 下载，PDF 用 Zotero 自带「Find Available PDF」补）

## 三步用法

1. **检索**（Tab ①）：输入检索词 → 勾选 NCBI/Scholar → 开始检索 → 候选列表勾选 → 「加入入库队列」
   - Scholar 条目自动用 Crossref 补全 DOI
2. **知网**（Tab ②）：浏览器打开知网详情页（保持 IP 登录）→ Ctrl+A 全选 → Ctrl+C → 粘贴 → 「解析」
3. **入库**（Tab ③）：选/输入 Zotero 合集名 → 刷新合集 → 「一键入库」
   - 每篇自动建父条目 + 笔记（摘要模板），可在表格「备注/笔记」列双击编辑
   - 学位论文自动识别（博士/硕士 + 学校字段）

## 配置（Tab ④，首次使用必填）

| 项 | 必填 | 说明 |
|---|---|---|
| Zotero API Key | ✅ 必填 | 自己的 key：zotero.org/settings/keys 新建 |
| Zotero User ID | ✅ 必填 | 自己的账号：zotero.org/settings 页面可见 |
| NCBI API Key | 建议 | ncbi.nlm.nih.gov/account/settings，不填会限速 |
| 代理地址 | 按需 | 默认 http://127.0.0.1:7897（Clash 类工具），不用代理取消勾选 |
| AI API Key | 可选 | 百炼/DeepSeek key，填了才有「✨ AI 打标签+笔记」 |
| AI 模型 | 可选 | 默认 qwen3.7-flash（便宜）；可换 deepseek-chat 等 |

首次启动会自动跳到设置页引导填写；填完点「保存设置」→「测试 Zotero 连接」。
配置存于 `config.json`（exe 同级目录，便携）。**API Key 为明文，分发软件/备份时不要带 config.json。**

## AI 打标签 + 笔记（可选）

在「③ 入库」页点「✨ AI 打标签+笔记（勾选）」：为勾选文献批量生成**语义标签**（研究方向/物种/机制，如 `白念珠菌` `自噬` `TORC1`）+ **中文阅读笔记**（核心内容 + 可借鉴方法）。

- 成本约 1 厘/篇（qwen3.7-flash）；后台线程不卡界面；单篇失败自动跳过
- 不配 AI key 则用规则标签（来源/类型），功能禁用

## 给他人使用

1. 只分发 `PaperLister.exe` + `README.md`（zip 内不含任何个人配置）
2. 对方首次打开 → 自动进入设置页 → 填写**自己的** Zotero/NCBI key → 即可使用

## 网络路由（重要）

- **NCBI / Google Scholar**：走代理（127.0.0.1:7897，需 Clash 类工具运行）
- **Zotero API**：直连（国内可直连，不走代理）
- **知网**：完全在你自己的浏览器里操作（保持机构 IP 登录态），软件只做文本解析，不碰浏览器

## 已知限制

- 知网为「粘贴文本半自动」：需手动复制详情页内容（规避 clickWord 验证码的刻意设计）
- Google Scholar 反爬偶发失败：自动跳过该查询，可重试
- 不做 PDF 下载：入库后在 Zotero 里右键条目 → Find Available PDF 自动找 OA 全文；或攒批找 AI 批量补

## 开发

```
pip install PySide6 pyinstaller pillow requests
python main.py                  # 运行
python smoke_test.py            # 核心模块测试
python gui_smoke.py             # GUI 测试
python e2e_test.py              # 端到端测试（真实检索）
python make_icon.py             # 重新生成图标
python -m PyInstaller --noconfirm --onefile --windowed --name PaperLister --icon app.ico main.py
```
