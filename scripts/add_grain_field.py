#!/usr/bin/env python3
"""一次性脚本：给 references/engineering-50.md 与 academic-50.md 每条 checklist
插入 `- **检查粒度**：xxx` 字段，直接位于 `### XXX-XX` 标题行之后。

粒度档位：
- skeleton          仅骨架元信息或骨架抽取的标题/关键句
- chunks            需要全文切块文本
- page-image        需要渲染原 PDF 页为图像
- refs-block        仅参考文献区段
- 组合用 + 连接（如 refs-block+chunks）

设计原则：边界 case 一律推到 chunks，优先评审质量。
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENG = REPO / "references" / "engineering-50.md"
ACA = REPO / "references" / "academic-50.md"

ENGINEERING_GRAIN = {
    # 红线
    "ENG-RED-1": "chunks",            # 抄袭/伪造：抽 100+ 字段落比对
    "ENG-RED-2": "skeleton+chunks",   # 文不对题：标题切词靠骨架，命中数靠 chunks
    "ENG-RED-3": "skeleton",          # 正文篇幅：页码 metadata
    "ENG-RED-4": "skeleton",          # 工作量饱满度：页码 metadata
    "ENG-RED-5": "chunks",            # 占位文本散落段落中
    # 学术质量
    "ENG-A-01": "chunks",             # 摘要-正文双向 grep
    "ENG-A-02": "chunks",             # 读完整摘要
    "ENG-A-03": "chunks",             # 读第一章前 3 页
    "ENG-A-04": "chunks",             # 后文命中数 grep
    "ENG-A-05": "chunks",             # 各技术小节首尾段
    "ENG-A-06": "chunks",             # 段落级"基础概念介绍"判定
    "ENG-A-07": "skeleton",           # 第二章页数
    "ENG-A-08": "chunks",             # 横向对比表识别
    "ENG-A-09": "chunks",             # 创新点列点判定
    "ENG-A-10": "chunks",             # 词频 + 语义对应
    "ENG-A-11": "chunks",             # 用例文本关键词 grep（限第三章）
    "ENG-A-12": "chunks",             # 4+1 视图关键词 grep
    "ENG-A-13": "chunks",             # ER/字段/SQL 一致性
    "ENG-A-14": "chunks",             # 模块名跨摘要/目录/章节比对
    "ENG-A-15": "skeleton+page-image",# 骨架定位 + 渲染图所在页
    "ENG-A-16": "chunks",             # 测试章关键词 grep
    "ENG-A-17": "chunks",             # 性能数字 grep
    "ENG-A-18": "chunks",             # 安全 keywords
    "ENG-A-19": "chunks",             # LLM 指标
    "ENG-A-20": "chunks",             # LLM 安全机制
    "ENG-A-22": "chunks",             # 量化对比词
    "ENG-A-23": "chunks",             # 数据一致性
    "ENG-A-24": "page-image",         # 界面截图视觉判定
    "ENG-A-25": "chunks",             # 选型对比段落
    "ENG-A-26": "chunks",             # 末尾章前 3 段
    "ENG-A-27": "chunks",             # 国内外对照段落
    "ENG-A-28": "chunks",             # 决策点论证段落
    # 结构内容
    "ENG-S-01": "skeleton",           # 目录结构
    "ENG-S-02": "chunks",             # 第一章末尾
    "ENG-S-03": "chunks",             # 各章末尾本章小结
    "ENG-S-04": "skeleton",           # 章节标题
    "ENG-S-05": "chunks",             # 摘要篇幅+模块名
    "ENG-S-06": "chunks",             # 中英文摘要段落对应
    "ENG-S-07": "chunks",             # 英文摘要 thesis 用词
    "ENG-S-08": "chunks",             # 抽样小节
    "ENG-S-09": "chunks",             # 全文术语 grep
    "ENG-S-10": "chunks",             # 读致谢
    "ENG-S-11": "chunks",             # 全文"如图 X.Y"grep
    # 参考文献
    "ENG-F-01": "refs-block+chunks",  # 双向匹配
    "ENG-F-02": "refs-block",         # 年份/类型分布
    "ENG-F-03": "refs-block",         # 中英文期刊核对
    "ENG-F-04": "refs-block+chunks",  # 正文引用格式 + 文献条目格式
    "ENG-F-05": "refs-block",         # 域名分类
}

ACADEMIC_GRAIN = {
    # 红线
    "ACA-RED-1": "chunks",
    "ACA-RED-2": "skeleton+chunks",
    "ACA-RED-3": "skeleton",
    "ACA-RED-4": "skeleton",
    "ACA-RED-5": "chunks",            # 形式化/伪代码/实验设置 grep
    # 学术质量（30 条）
    "ACA-A-01": "chunks",             # 摘要四要素
    "ACA-A-02": "chunks",             # RQ 形式判定
    "ACA-A-03": "chunks",             # 贡献声明
    "ACA-A-04": "chunks",             # 创新点-消融对照
    "ACA-A-05": "chunks",             # 第二章组织
    "ACA-A-06": "refs-block",         # 文献年份分布
    "ACA-A-07": "chunks",             # 问题形式化
    "ACA-A-08": "chunks",             # 方法描述详实度
    "ACA-A-09": "chunks",             # 伪代码识别
    "ACA-A-10": "chunks",             # 数据集说明
    "ACA-A-11": "chunks",             # 偏差讨论
    "ACA-A-12": "chunks",             # 评价指标列表
    "ACA-A-13": "chunks",             # 基线列表
    "ACA-A-14": "chunks",             # 实验设置
    "ACA-A-15": "chunks",             # 消融实验
    "ACA-A-16": "chunks",             # 显著性
    "ACA-A-17": "chunks",             # 横向对比表
    "ACA-A-18": "chunks",             # case study
    "ACA-A-19": "chunks",             # 失败原因
    "ACA-A-20": "chunks",             # 泛化能力
    "ACA-A-21": "chunks",             # 计算开销
    "ACA-A-22": "chunks",             # 效度讨论
    "ACA-A-23": "chunks",             # LLM 类
    "ACA-A-24": "chunks",             # 局限性
    "ACA-A-25": "chunks",             # 相关工作-本文对照
    "ACA-A-26": "skeleton",           # 工程章 vs 方法实验章页数比例
    "ACA-A-27": "chunks",             # 展望-局限对应
    "ACA-A-28": "chunks",             # 公式符号一致性
    "ACA-A-29": "refs-block",         # arXiv/顶会引用统计
    "ACA-A-30": "skeleton",           # 第二章页数
    # 结构内容
    "ACA-S-01": "skeleton",
    "ACA-S-02": "chunks",
    "ACA-S-03": "chunks",
    "ACA-S-04": "chunks",             # 摘要篇幅+实验数据
    "ACA-S-05": "chunks",             # 英文摘要对应
    "ACA-S-06": "chunks",             # 标题与内容
    "ACA-S-07": "chunks",             # 术语+符号一致
    "ACA-S-08": "chunks",             # 致谢
    "ACA-S-09": "chunks",             # 章节结构
    "ACA-S-10": "chunks",             # 方法/实验切分
    # 参考文献
    "ACA-F-01": "refs-block+chunks",  # 双向
    "ACA-F-02": "refs-block",         # 文献质量
    "ACA-F-03": "refs-block+chunks",  # 引用格式
    "ACA-F-04": "chunks",             # 公式格式（图片/编号引用）需读正文
    "ACA-F-05": "chunks",             # 图表/算法/公式编号连续性需全文
    "ACA-F-06": "refs-block",         # 非同行评议来源
}


def add_grain(content: str, grain_map: dict) -> tuple[str, list[str]]:
    """在每个 `### XXX-XX -- 标题` 行后插入 `- **检查粒度**：grain` 行。

    返回 (新内容, 未匹配 ID 列表)。
    """
    seen = set()
    missing_in_map = []

    def replace(match):
        heading_line = match.group(0)
        item_id = match.group(1)
        seen.add(item_id)
        grain = grain_map.get(item_id)
        if grain is None:
            missing_in_map.append(item_id)
            return heading_line  # 不动
        return f"{heading_line}\n- **检查粒度**：{grain}"

    # 仅匹配 ENG-XXX-NN 或 ACA-XXX-NN 形式的子标题
    new_content = re.sub(
        r"^### ((?:ENG|ACA)-[A-Z]+-\d+)\b.*$",
        replace,
        content,
        flags=re.MULTILINE,
    )

    missing_in_file = [k for k in grain_map if k not in seen]
    return new_content, missing_in_map, missing_in_file


def process(path: Path, grain_map: dict) -> None:
    text = path.read_text(encoding="utf-8")
    if "**检查粒度**" in text:
        print(f"[skip] {path.name}：已含 `检查粒度` 字段，未重复写入。")
        return
    new_text, missing_in_map, missing_in_file = add_grain(text, grain_map)
    if missing_in_map:
        print(f"[warn] {path.name}：以下条目在文件中存在但 grain map 未定义：{missing_in_map}")
    if missing_in_file:
        print(f"[warn] {path.name}：以下 ID 在 grain map 中但文件未找到：{missing_in_file}")
    path.write_text(new_text, encoding="utf-8")
    print(f"[ok]   {path.name}：写入完成。")


if __name__ == "__main__":
    process(ENG, ENGINEERING_GRAIN)
    process(ACA, ACADEMIC_GRAIN)
