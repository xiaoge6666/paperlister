# PaperLister v0.1.0 Release Notes

## 简介

知网 + NCBI/PubMed + Google Scholar 多源文献**题录**检索 → 一键入库 Zotero 的 Windows 便携工具。

- 纯题录版：不做 PDF 下载，PDF 用 Zotero 自带「Find Available PDF」补
- 四页签：检索 / 知网解析 / Zotero 入库 / 设置
- 可选「✨ AI 打标签 + 笔记」（OpenAI 兼容接口，默认 qwen3.7-flash，约 1 厘/篇）

## 下载

下载 Assets 中的 `PaperLister_v0.1.0.zip`，解压整个文件夹后运行 `PaperLister.exe`。
不要只复制单个 exe。

## 安装与首次使用

1. 解压 zip 到任意目录
2. 双击 `PaperLister.exe`
3. 首次启动自动进入设置页，填写**你自己的** Zotero / NCBI / 代理 / AI 配置
4. 保存后即可使用

## 变更

- v0.1.0：首个公开版本
  - NCBI + Google Scholar 检索（Scholar 自动 Crossref 补 DOI）
  - 知网详情页粘贴文本解析（规避 clickWord 验证码的半自动设计）
  - Zotero 入库：父条目 + 中文笔记 + 标签，学位论文自动识别
  - 设置页完整配置引导 + 连接测试

## 校验

- 文件：`PaperLister_v0.1.0.zip`（48.4 MB）
- SHA256：`A6C15799C6795B7CE4BD291EF1B7CBB2C1B1705B6CE8B7527E7919EAE0D60E36`

## 开源

- 源码仓库：https://github.com/xiaoge6666/paperlister
- License：MIT
