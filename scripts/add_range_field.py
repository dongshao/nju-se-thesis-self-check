#!/usr/bin/env python3
"""一次性脚本：给 references/engineering-50.md 与 academic-50.md 每条 checklist
在 `- **检查粒度**：xxx` 之后追加 `- **检查范围**：xxx` 字段。

范围词表（与 SKILL.md 步骤 1.5 chunk 命名对齐）：
  metadata        骨架元信息（页数、章数）
  cover-info      封面页
  toc             目录
  abstract-cn     中文摘要
  abstract-en     英文摘要
  ch1 / ch2 / ch3 / ch4 / ch5 / last-ch
  ch3-end         第三章及以后
  design-impl     设计/实现章（工程型动态识别）
  test-ch         系统测试章
  methods-ch      方法章（学术型）
  experiment-ch   实验章（学术型）
  all-body        全部正文章
  acknowledgement 致谢
  references      参考文献区段
  figures         渲染图所在页
  screenshots     界面截图所在页

多区段用 + 连接。
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENG = REPO / "references" / "engineering-50.md"
ACA = REPO / "references" / "academic-50.md"

ENGINEERING_RANGE = {
    # 红线
    "ENG-RED-1": "ch2+design-impl",                         # 抽段对比 + 截图前后矛盾
    "ENG-RED-2": "cover-info+ch3-end",                      # 标题关键词在第三章及以后命中
    "ENG-RED-3": "metadata",
    "ENG-RED-4": "metadata",
    "ENG-RED-5": "all-body+acknowledgement",                # 占位文本散布全文
    # 学术质量
    "ENG-A-01": "abstract-cn+ch3-end",                      # 摘要关键词命中正文
    "ENG-A-02": "abstract-cn",                              # 摘要四要素
    "ENG-A-03": "ch1",                                      # 第一章前 3 页
    "ENG-A-04": "ch2+ch3-end",                              # 第二章技术词 -> 后文命中
    "ENG-A-05": "ch2",                                      # 各技术小节作用说明
    "ENG-A-06": "ch2",                                      # 低水平技术
    "ENG-A-07": "metadata",                                 # 第二章页数
    "ENG-A-08": "ch2+last-ch",                              # 横向对比
    "ENG-A-09": "ch1+last-ch",                              # 创新点声明
    "ENG-A-10": "cover-info+abstract-cn+ch1+last-ch",       # "智能"等词频
    "ENG-A-11": "ch3",                                      # 用例图+用例文本（限第三章）
    "ENG-A-12": "ch3",                                      # 4+1 视图
    "ENG-A-13": "ch3+ch4",                                  # ER/字段/SQL 一致性
    "ENG-A-14": "abstract-cn+toc+ch3-end",                  # 模块名跨段比对
    "ENG-A-15": "cover-info+figures",                       # 标题 + 功能结构图
    "ENG-A-16": "test-ch",                                  # 系统测试章节
    "ENG-A-17": "test-ch",                                  # 性能量化指标
    "ENG-A-18": "ch3+ch4",                                  # 安全设计
    "ENG-A-19": "all-body",                                 # LLM 类先判型再统计
    "ENG-A-20": "all-body",                                 # LLM 安全机制
    "ENG-A-21": "test-ch",                                  # 失败案例
    "ENG-A-22": "abstract-cn+ch1+last-ch+test-ch",          # 业务价值量化
    "ENG-A-23": "ch3+ch4",                                  # 数据一致性
    "ENG-A-24": "screenshots",                              # 界面截图视觉
    "ENG-A-25": "ch2",                                      # 技术原理深度
    "ENG-A-26": "last-ch",                                  # 末尾章总结具体性
    "ENG-A-27": "ch1+ch2",                                  # 国内外对照（可放第一/第二章）
    "ENG-A-28": "ch3",                                      # 关键设计决策论证
    # 结构内容
    "ENG-S-01": "toc",
    "ENG-S-02": "ch1",                                      # 第一章末尾【本文组织结构】
    "ENG-S-03": "all-body",                                 # 各章末尾本章小结
    "ENG-S-04": "toc",
    "ENG-S-05": "abstract-cn",
    "ENG-S-06": "abstract-cn+abstract-en",
    "ENG-S-07": "abstract-en",
    "ENG-S-08": "all-body",                                 # 抽 5 节比对标题与内容
    "ENG-S-09": "all-body",                                 # 全文术语别名
    "ENG-S-10": "acknowledgement",
    "ENG-S-11": "all-body",                                 # 全文"如图 X.Y 所示"
    # 参考文献
    "ENG-F-01": "references+all-body",                      # 双向匹配
    "ENG-F-02": "references",
    "ENG-F-03": "references",
    "ENG-F-04": "references+all-body",                      # 引用格式在正文
    "ENG-F-05": "references",
}

ACADEMIC_RANGE = {
    # 红线
    "ACA-RED-1": "ch2+experiment-ch",
    "ACA-RED-2": "cover-info+methods-ch+experiment-ch",
    "ACA-RED-3": "metadata",
    "ACA-RED-4": "metadata",
    "ACA-RED-5": "ch2+methods-ch+experiment-ch",            # 形式化/伪代码/实验设置
    # 学术质量
    "ACA-A-01": "abstract-cn",                              # 摘要四要素
    "ACA-A-02": "ch1",                                      # 第一章 RQ
    "ACA-A-03": "ch1+last-ch",                              # 创新点声明
    "ACA-A-04": "ch1+methods-ch+experiment-ch",             # 创新点-消融对照
    "ACA-A-05": "ch2",                                      # 第二章组织
    "ACA-A-06": "references",                               # 文献年份分布
    "ACA-A-07": "methods-ch",                               # 问题形式化
    "ACA-A-08": "methods-ch",                               # 方法详实度
    "ACA-A-09": "methods-ch",                               # 算法伪代码
    "ACA-A-10": "experiment-ch",                            # 数据集说明
    "ACA-A-11": "experiment-ch+last-ch",                    # 数据集偏差讨论
    "ACA-A-12": "experiment-ch",                            # 评价指标
    "ACA-A-13": "experiment-ch+references",                 # 基线选择
    "ACA-A-14": "experiment-ch",                            # 实验设置
    "ACA-A-15": "experiment-ch",                            # 消融实验
    "ACA-A-16": "experiment-ch",                            # 统计显著性
    "ACA-A-17": "experiment-ch",                            # 横向对比表
    "ACA-A-18": "experiment-ch",                            # case study
    "ACA-A-19": "experiment-ch",                            # 失败原因分析
    "ACA-A-20": "experiment-ch",                            # 泛化能力
    "ACA-A-21": "experiment-ch",                            # 计算开销
    "ACA-A-22": "experiment-ch+last-ch",                    # 效度讨论
    "ACA-A-23": "all-body",                                 # LLM 类
    "ACA-A-24": "last-ch",                                  # 局限诚实
    "ACA-A-25": "ch2+methods-ch+experiment-ch",             # 相关工作-本文对照
    "ACA-A-26": "metadata",                                 # 工程章 vs 方法实验章页比
    "ACA-A-27": "last-ch",                                  # 展望-局限对应
    "ACA-A-28": "methods-ch+experiment-ch",                 # 公式符号一致性
    "ACA-A-29": "references",                               # arXiv/顶会引用
    "ACA-A-30": "metadata",                                 # 第二章页数
    # 结构内容
    "ACA-S-01": "toc",
    "ACA-S-02": "ch1",
    "ACA-S-03": "all-body",
    "ACA-S-04": "abstract-cn",
    "ACA-S-05": "abstract-cn+abstract-en",
    "ACA-S-06": "all-body",
    "ACA-S-07": "all-body",
    "ACA-S-08": "acknowledgement",
    "ACA-S-09": "methods-ch+experiment-ch",
    "ACA-S-10": "toc+ch3+ch4",
    # 参考文献
    "ACA-F-01": "references+all-body",
    "ACA-F-02": "references",
    "ACA-F-03": "references+all-body",
    "ACA-F-04": "methods-ch+all-body",                      # 公式格式
    "ACA-F-05": "all-body",                                 # 编号连续性
    "ACA-F-06": "references",
}


def add_range(content: str, range_map: dict) -> tuple[str, list[str], list[str]]:
    """在 `- **检查粒度**：grain` 行之后插入 `- **检查范围**：range` 行。

    匹配模式：先定位 `### XXX-XX` 标题，再找紧随其后的 `- **检查粒度**：` 行。
    """
    seen = set()
    missing_in_map = []

    def repl(match):
        item_id = match.group(1)
        seen.add(item_id)
        rng = range_map.get(item_id)
        if rng is None:
            missing_in_map.append(item_id)
            return match.group(0)  # 不动
        # match.group(0) = "### ID — title\n- **检查粒度**：grain"
        return f"{match.group(0)}\n- **检查范围**：{rng}"

    new_content = re.sub(
        r"^### ((?:ENG|ACA)-[A-Z]+-\d+)\b[^\n]*\n- \*\*检查粒度\*\*：[^\n]+",
        repl,
        content,
        flags=re.MULTILINE,
    )

    missing_in_file = [k for k in range_map if k not in seen]
    return new_content, missing_in_map, missing_in_file


def process(path: Path, range_map: dict) -> None:
    text = path.read_text(encoding="utf-8")
    if "**检查范围**" in text:
        print(f"[skip] {path.name}：已含 `检查范围` 字段，未重复写入。")
        return
    new_text, missing_in_map, missing_in_file = add_range(text, range_map)
    if missing_in_map:
        print(f"[warn] {path.name}：以下条目在文件中存在但 range map 未定义：{missing_in_map}")
    if missing_in_file:
        print(f"[warn] {path.name}：以下 ID 在 range map 中但文件未找到：{missing_in_file}")
    path.write_text(new_text, encoding="utf-8")
    print(f"[ok]   {path.name}：写入完成。")


if __name__ == "__main__":
    process(ENG, ENGINEERING_RANGE)
    process(ACA, ACADEMIC_RANGE)
