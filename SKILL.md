---
name: nju-se-thesis-self-check
description: 给南京大学软件学院、智能软件与工程学院专业学位硕士论文送审前的自检 skill。学生提供论文 PDF，先从 PDF 摘要页/封面抽取真实论文题目并请学生确认，再自动判定"工程型 / 学术型"并请学生确认，按对应类别的 checklist（工程型 48 条 / 学术型 51 条，含 5 条红线）逐项审查，给出带原文页码定位的反馈、红线高亮、评议结论估计，最后写到 <论文同目录>/<论文题目>-review.md（题目来自 PDF 内容而非文件名）。仅在用户明确说"论文自检""自查""送审前自查""我的论文有什么问题"等触发词且提供 PDF 路径时启用。
---

# NJU SE专硕论文自检 skill

给学生送审前自查用。本 skill 是学生视角的 checklist 逐项审查。

## 何时使用

仅在用户明确说出以下触发词之一**且**提供论文 PDF 路径时启用：
- 「论文自检」「论文自查」「送审前自查」
- 「我的论文有什么问题」「我的论文能过吗」
- 「self-check」「pre-defense check」

不要只看到 PDF 就触发。

## 调用格式

```
论文自检 /path/to/paper.pdf
论文自检 /path/to/paper.pdf --type=engineering   # 跳过类型判定
论文自检 /path/to/paper.pdf --type=academic
论文自检 /path/to/paper.pdf --auto              # 全自动模式
```

`--type` 可选值：`engineering`（工程型）/ `academic`（学术型）。

`--auto` 触发**全自动模式**：用户消息中含「全自动」「自动模式」「auto」「--auto」「-y」「yes to all」任一关键词即视为开启。

## 全自动模式（AUTO_MODE）

开启后，整条流程从步骤 1 跑到步骤 9 一气呵成，**任何 Gate 都不再向用户索要确认**——本 skill 的 Claude 用自己的判断直接通过。具体差异如下：

| 环节 | 缺省（人工模式） | 全自动模式 |
|---|---|---|
| 步骤 1 抽题确认 | 把抽到的题目贴出来，等 y / 纠正 | 直接用抽到的 `title_clean` 作为最终题目，不询问；如三种策略全部失败回退到文件名，写入报告"附注：题目抽取退化"段 |
| 步骤 1 骨架异常 | 列出问题，问是否继续 | 直接继续；把骨架异常情况写入报告"附注：骨架异常"段 |
| 步骤 2 类别判定 | 给判定+证据，等 y / 纠正 | 用判定结果直接进入步骤 3；把判定证据写入报告"类别判定依据"段 |
| 步骤 6 图表能力探针失败 | 提示用户并跳过本步 | 自动跳过；在报告第六节写明"当前模型不支持图像输入，跳过 UML 图形评估，仅做基于图注的文本检查" |
| 步骤 9 是否做文风检查 | 询问用户 y/n | 默认进行；如未安装 humanizer-zh 则跳过并在报告第八节顶部写明"未安装 humanizer-zh，本节仅含错别字检查" |

全自动模式下需保留的硬停点（**不能跳过**）：
- 论文 PDF 路径不存在 / 不是 PDF → 报错并停止
- `pdfplumber` 未安装 → 报错并提示 `pip install pdfplumber`，停止
- 步骤 1 骨架抽取脚本崩溃（非"骨架不完整"，是真的崩） → 报错并停止
- 步骤 3.2 切块脚本崩溃 → 报错并停止；脚本本身正常但 `split_failed=true` 或 `body_chars < 5000` → 不停止，进入"骨架降级模式"（粒度=chunks 的条目降级为基于骨架判定），并在报告头部加警示
- 步骤 6 PyMuPDF 未安装 → 不停止，跳过步骤 6 并在报告第六节写明"PyMuPDF 未安装，请运行 pip install pymupdf 后重跑"
- 步骤 9 复用步骤 3.2 chunks；如步骤 3.2 已降级 → 跳过步骤 9 并在报告里写明原因

全自动模式下需在**对话中实时输出**关键节点，让用户看到进度（一句话一节点即可）：

```
[1/9] 抽骨架完成（{pages} 页 / {chapters} 章）
[1/9] 题目：《...》
[2/9] 类别：工程型（依据：第三章"系统架构"+ 第五章"系统测试"）
[3/9] 已加载 engineering-50.md（48 条）+ 切块（N 块 / body_chars≈X / split_failed=false）
[4/9] 红线扫描：命中 X 条
[5/9] 全量审查完成：✅ A / ⚠️ B / ❌ C
[6/9] 图表规范性：识别 N 张图 / 命中 M 类图 / 警告 K 条
[7/9] 报告写入 {report_path}
[8/9] 摘要：预估评议结论 {结论}
[9/9] 文风+错别字检查：复用 N 块 chunks / 错别字 X 条 / 文风 Y 条
完成。
```

人工模式下保持原行为不变。

## 前置依赖

- `pdfplumber`：如缺失提示用户 `pip install pdfplumber`
- `PyMuPDF`（包名 `pymupdf`，import 名 `fitz`）：步骤 6 渲染整页为 PNG。如缺失提示 `pip install pymupdf`；缺失只导致步骤 6 跳过，不影响其他步骤
- 本 skill 自带 `scripts/extract_skeleton.py`（步骤 1 抽骨架）与 `scripts/extract_chunks.py`（步骤 3.2 全文切块），无需依赖外部 skill

## 输出位置约定

- **最终报告** → `<论文 PDF 所在目录>/<论文题目>-review.md`（学生第一眼能看到）；如已存在则顺延为 `<论文题目>-review-1.md` / `-review-2.md` / ...，**不覆盖前次报告**，便于学生对照修改进度。具体路径由步骤 7 生成的 `$REPORT_PATH` 决定
- **中间产物** → `<论文 PDF 所在目录>/<TMP_DIR>/`，`<TMP_DIR>` 由步骤 1 顺延决定：默认 `tmp`，若已存在则改用 `tmp1` / `tmp2` / ... 直到找到未占用的目录名。**不覆盖前次产物**，学生可对比多次跑的差异。下文为可读性以 `tmp/` 占位指代当前实际目录。
  - `<TMP_DIR>/skeleton.md` — 步骤 1 抽出的骨架
  - `<TMP_DIR>/chunks/<range>.txt` — 步骤 3.2 按范围切分的全文（如 `ch1.txt` / `abstract-cn.txt` / `references.txt` / `acknowledgement.txt`）
  - `<TMP_DIR>/chunks/chunks-index.json` — 步骤 3.2 的 chunk 索引 + 动态范围映射 + split_failed 标志
  - `<TMP_DIR>/figs/page-NNN.png` — 步骤 6 渲染的关键图所在页
  - 步骤 9（文风+错别字）复用 `<TMP_DIR>/chunks/`，不再二次切分

不要再往 `/tmp/` 系统临时目录写——重启会丢，也不便于学生回看；也不要把中间产物直接散落在论文目录下。`<paper_dir>/<TMP_DIR>/` 是唯一中转区。

## 步骤执行原则（**强制**）

1. **不得为节省 token / 时间跳过任何步骤或子步骤**——只要前置依赖满足且未触发 SKILL.md 明文允许的退化分支，本 skill 就必须把每个步骤完整跑完。学生付费跑一次自检的预期是「完整审查」，跳过等于交付残缺产品。
2. **仅以下情形允许跳过**：
   - PDF 文件不存在 / 不是 PDF → 整体停止
   - 必需依赖缺失（pdfplumber / PyMuPDF）→ 按 SKILL.md 各步骤明文规定的退化路径处理（如步骤 6 缺 PyMuPDF 时跳过本步骤；不是绕过，必须在最终报告里写明跳过原因 + 安装命令）
   - 模型图像能力探针失败（VISION_CAPABLE=false）→ 步骤 6 进退化路径，仍要做基于图注的文本检查
   - 步骤 9 学生明确选「n 跳过」（人工模式下询问后），或 humanizer-zh 未安装（AUTO_MODE 下降级为仅错别字）
3. **不得编造"未执行"措辞**：报告里如果写了某步骤"未执行"或"跳过"，必须给出具体原因（依赖缺失 / 探针失败 / 用户拒绝），不能是"为节省时间"。
4. **token 不是借口**：本 skill 设计上预期一次完整跑可能消耗较多 token——这是学生选择跑自检时已知的成本。跳步骤换"看起来跑完了"是对学生的欺骗。

## 主流程（8 步 + 1 步可选）

### 步骤 1：抽骨架 + 抽取论文题目

```bash
PAPER_PDF="/path/to/paper.pdf"
PAPER_DIR=$(dirname "$PAPER_PDF")

# tmp 目录顺延：默认 tmp；已存在则 tmp1 / tmp2 / ... 找首个未占用的
# 不要复用或覆盖前次 tmp 目录——学生可能还要回看上一次的 chunks / figs / skeleton
TMP_DIR="$PAPER_DIR/tmp"
i=1
while [ -e "$TMP_DIR" ]; do
  TMP_DIR="$PAPER_DIR/tmp$i"
  i=$((i+1))
done
mkdir -p "$TMP_DIR"
echo "TMP_DIR=$TMP_DIR"   # 后续步骤的 Python 代码块从这里读取实际目录

python3 ~/.claude/skills/nju-se-thesis-self-check/scripts/extract_skeleton.py \
  "$PAPER_PDF" \
  --out "$TMP_DIR/skeleton.md"
```

**重要**：本次会话内所有后续步骤（3.2 切块 / 6 渲染图 / 9 文风检查）必须用同一个 `$TMP_DIR`。Bash 工具的 shell state 不跨 call 持久，所以**记住步骤 1 echo 出的路径**，在后续每个 Bash / Python 代码块的开头**显式重赋值**（Bash 用 `TMP_DIR="..."`；Python 用 `TMP_DIR = "..."`）。**不要**在后续步骤里再跑一次顺延逻辑——那会建一个新的空目录。

下文 SKILL.md 里的 Python 代码块写成 `TMP_DIR = os.environ["TMP_DIR"]` 仅作示意，**实际执行前请把它替换成步骤 1 实际 echo 出的绝对路径字符串**。

读骨架。如脚本失败 / 骨架 < 30 页 / 章节切分退化（出现"未识别章节"）：
- 先告知用户骨架异常，列出问题，问是否继续（基于不完整骨架审查会漏检）。
- **AUTO_MODE**：不询问，直接继续；把异常情况写到最终报告"附注：骨架异常"段（脚本崩溃除外，那种情况必须停）。

**抽取论文题目**（用于步骤 7 的报告文件名）。骨架脚本读 PDF metadata，但 NJU 论文 PDF 的 metadata 标题常常是模板填充字段或文件 ID（如 `01KQ3VJY7RVK44...`），不可信。改用如下策略，按优先级取最先成功者：

```python
# 直接从 PDF 前 10 页提取头部文本来找题目
# 优先级 1：摘要首页"毕业论文题目：" 行（最干净，单行完整）
# 优先级 2：封面"论 文 题 目" 区段（多行，需要合并）
# 优先级 3：fallback 到 PDF 文件名（极少数情况）

import re, pdfplumber
PDF = "/path/to/paper.pdf"
title = None

with pdfplumber.open(PDF) as pdf:
    head_text = '\n'.join((p.extract_text() or '') for p in pdf.pages[:10])

# 策略 1：抓"毕业论文题目：" 后续内容，直到下一字段
# 注意：pdfplumber 提取时部分 PDF 不会在标题尾与学生信息字段之间插入换行，
# 因此 stop word 不强制要求 \n 前缀，仅要求遇到典型字段名即停。
m = re.search(
    r'毕业论文题目[：:]\s*([\s\S]{1,150}?)(?=(?:工程硕士|专业学位|硕士生姓名|指导教师|学\s*校\s*代\s*码|软件工程专业|计算机.{0,4}专业|.{0,8}\d{4}\s*级\s*硕士生))',
    head_text
)
if m:
    title = re.sub(r'\s+', '', m.group(1)).strip()

# 策略 2：从封面"论 文 题 目"开始抓多行直到"作者姓名"或"学位类别"前
if not title:
    m = re.search(r'论\s*文\s*题\s*目\s*([\s\S]{0,200}?)(?=作\s*者\s*姓\s*名|专业学位类别|研\s*究\s*方\s*向)', head_text)
    if m:
        # 折叠多行/多空格为无空格（中文标题中间不需要空格）
        title = re.sub(r'\s+', '', m.group(1)).strip()

# 策略 3：fallback
if not title or len(title) < 5:
    import os
    title = os.path.splitext(os.path.basename(PDF))[0]
    print(f"警告：未能从 PDF 内容抽取题目，回退到文件名: {title}")

# 清洗为合法文件名：去除路径分隔符、控制字符、多余空格
title_clean = re.sub(r'[\\/:*?"<>|\r\n\t]', '', title).strip()
# 极长截断：>120 字符截断（防 macOS 文件名 255 字节限制）
if len(title_clean) > 120:
    title_clean = title_clean[:120]
print(f"PAPER_TITLE={title_clean}")
```

把得到的 `title_clean` 存为环境变量 `PAPER_TITLE` 或 shell 变量，供步骤 7 拼接报告路径使用。

**告诉用户抽取到的题目**，让用户确认或纠正：

```
从 PDF 抽取到的论文题目：
《{title_clean}》

报告将写到：<论文同目录>/{title_clean}-review.md（如已存在则顺延为 -review-1.md / -review-2.md / ...）

确认输入 y 继续；如题目错误请直接给出正确题目。
```

**AUTO_MODE**：不询问，直接采用 `title_clean` 作为最终题目继续步骤 2。如果走到了策略 3（fallback 到文件名），在最终报告"附注：题目抽取退化"段写明，仍继续。

### 步骤 2：类别判定 Gate

读骨架的元信息 + 各章首页文本，按以下规则判别：

| 信号 | 工程型 | 学术型 |
|---|---|---|
| 第二章篇幅与重心 | 偏"技术栈介绍"（Spring、K8s、LLM 框架等） | 偏"相关工作综述"（按方法/路线分类） |
| 第三/四章 | "需求分析 / 系统架构 / 详细设计 / 实现" | "问题形式化 / 模型设计 / 实验设计" |
| 是否有"系统测试"章 | 通常有 | 通常无 |
| 是否有"实验对比"章 | 弱（功能验证为主） | 强（基线对比 + 消融） |
| 关键句信号词 | "本系统"、"模块"、"部署"、"接口" | "提出"、"实验表明"、"结果表明"、"基线" |
| 摘要核心 | 系统的功能与工程价值 | 方法的创新与实验结论 |

**输出格式（无 emoji）**：

```
论文类型判别
------------------------------------------------------------
论文标题：[骨架中的标题]
我判定为：【工程型 / 学术型】
判定依据：
1. [一条具体证据，含章节或页码]
2. [第二条]
3. [第三条]

请确认：
- 输入 y / 工程 / 学术 来确认或纠正
- 如果是混合型，请告诉我重心偏向哪一类
```

如果用户提供了 `--type=...` 跳过本 Gate。

**AUTO_MODE**：不询问，直接采用本 skill 自己的判定结果进入步骤 3。判定证据写入最终报告"类别判定依据"段，便于学生回溯。如判定证据不足以单边定论（信号严重对半），按工程型处理（NJU 软院专硕以工程型居多，作为更稳妥的默认），并在报告里加注「类别存疑，建议人工复核」。

### 步骤 3：加载 checklist + 全文切块

#### 3.1 加载对应 checklist

根据确认的类别，读取对应文件：
- 工程型：`~/.claude/skills/nju-se-thesis-self-check/references/engineering-50.md`
- 学术型：`~/.claude/skills/nju-se-thesis-self-check/references/academic-50.md`

不要混读两份。条目分布：
- 工程型：5 条红线 + 27 条学术质量 + 11 条结构内容 + **5 条参考文献问题**（共 48 条）
- 学术型：5 条红线 + 30 条学术质量 + 11 条结构内容 + **5 条参考文献问题**（共 51 条）

每条 checklist 都带两个 dispatcher 字段，步骤 4-5 据此选择读取入口：

| 字段 | 取值 | 含义 |
|---|---|---|
| `检查粒度` | `skeleton` / `chunks` / `page-image` / `refs-block`（多值用 +） | HOW：用什么入口读 |
| `检查范围` | `metadata` / `cover-info` / `toc` / `abstract-cn` / `abstract-en` / `ch1`-`ch5` / `ch3-end` / `last-ch` / `design-impl` / `test-ch` / `methods-ch` / `experiment-ch` / `all-body` / `acknowledgement` / `references` / `figures` / `screenshots`（多值用 +） | WHERE：读哪段 |

#### 3.2 全文切块

调用 `extract_chunks.py` 把 PDF 按范围切成独立 .txt：

```bash
python3 ~/.claude/skills/nju-se-thesis-self-check/scripts/extract_chunks.py \
  "$PAPER_PDF" \
  --out "$TMP_DIR/chunks"
```

产物：
- `$TMP_DIR/chunks/<range>.txt`：每个固定范围一份原文，文件名严格对齐 `检查范围` 词表（如 `ch1.txt` / `abstract-cn.txt` / `acknowledgement.txt`）
- `$TMP_DIR/chunks/chunks-index.json`：含 `chunks`（每个文件的页码、字符数、章标题）+ `range_map`（动态范围如 `ch3-end` / `design-impl` / `test-ch` / `methods-ch` / `experiment-ch` / `last-ch` / `all-body` 映射到具体 `chN` 列表）+ `stats.split_failed` 标志

读 `chunks-index.json` 一次，缓存 `range_map` 在工作记忆里供步骤 4-5 dispatch 用。

**切块结果分支**：

| `stats.split_failed` | `stats.body_chars` | 处理 |
|---|---|---|
| false | ≥ 5000 | ✅ 正常进入步骤 4 |
| true | 任意 | ⚠️ "骨架降级模式"：所有 `检查粒度=chunks` 的条目改为基于骨架对应章节的关键句判定，质量下降但仍能跑完；最终报告头部加警示「全文切分失败，本次审查质量受限」 |
| false | < 5000 | ⚠️ 同上，且额外建议用户检查 PDF 是否扫描版（无文本层）|

人工模式下首次进入降级时告知用户并询问是否继续；AUTO_MODE 直接继续。

### 步骤 4：红线扫描（先跑 5 条）

先把 5 条红线跑一遍。每条按其 `检查粒度` + `检查范围` 字段选取读取入口：

| 检查粒度 | 读取入口 |
|---|---|
| `skeleton` | 读 `$TMP_DIR/skeleton.md`，按 `检查范围`（metadata/toc/cover-info）取相应段或元信息 |
| `chunks` | Read `$TMP_DIR/chunks/<range>.txt`；`检查范围` 是动态范围（`ch3-end` / `design-impl` / `test-ch` / `methods-ch` / `experiment-ch` / `last-ch` / `all-body`）时，先在 `$TMP_DIR/chunks/chunks-index.json` 的 `range_map` 里查到具体 ch 列表，再分别 Read |
| `page-image` | 渲染 PDF 对应页到 `$TMP_DIR/figs/`（沿用步骤 6 的 PyMuPDF 流程） |
| `refs-block` | Read `$TMP_DIR/chunks/references.txt` |

reference 文件里的"检查方法"段是这种粒度+范围下应执行的操作的细化（grep 模板、关键词、判定阈值）——按"检查方法"做，但**读取入口由本表决定**，不要再去骨架抽样代替全文。

**降级模式**：步骤 3.2 报告 `split_failed=true` 时，所有 `检查粒度=chunks` 项退回到骨架对应章节段。

记录红线命中数，不要在此停下，继续步骤 5。

### 步骤 5：全量审查（剩余条目）

按 reference 文件中的顺序逐条审查。每条遵循"评判 + 定位 + 修改建议"模式。

**读取策略**：与步骤 4 同表，按 `检查粒度` + `检查范围` 选取入口。

**扫描方向（必须"按范围分组"，理由是质量而非省 token）**：
1. 先把所有 `检查粒度=chunks` 的条目按 `检查范围` 分组：
   - `abstract-cn`：[ENG-A-02, ENG-S-05, ...]
   - `ch2`：[ENG-A-04, ENG-A-05, ENG-A-06, ENG-A-08, ENG-A-25]
   - `ch3-end`（先解析 range_map → ch3,ch4,...,last）：[ENG-RED-2, ENG-A-01, ENG-A-04, ENG-A-14]
   - `experiment-ch`（学术型）：[ACA-A-10, ACA-A-12, ..., 共 10+ 条]
2. 对每个范围 **Read 一次** 对应 `<range>.txt`（动态范围合并 range_map 内的 chN.txt），在同一个判定回合里把该范围下所有条目的判定一起输出。
3. 跨范围条目（如 ENG-A-14 同时涉及 `abstract-cn+toc+ch3-end`）放在最大的覆盖范围内主判，必要时补读小范围 chunk 做交叉核对。

按范围分组扫描的核心收益是**质量**：同一段原文里相关条目可以互为参照，交叉证据（前后矛盾、模块名一致性、数字一致性等）在同一上下文内一次看清，不会因条目级遍历跨次读取而被遗漏。token 量虽然顺带从「N 条 × M 个 chunk」降到「∑各范围字符数 × 1」，但这是副产物，不是选择该方式的理由——审查质量永远优先于 token 消耗。

**单条审查的内部模板**（合格项写一行；警告/不合格项展开）：

**单条审查的内部模板**（合格项写一行；警告/不合格项展开）：

```yaml
- id: ENG-A-12
  状态: ✅ / ⚠️ / ❌
  位置: P.42-44, §3.2.1（仅警告/不合格时给）
  评语: "评审专家口吻，1-3 句"（仅警告/不合格时给）
  修改建议: "具体怎么改"（仅警告/不合格时给）
```

**评语口吻参考**（来自实际评审意见）：
- 不写"你应该……"，写"建议在 X 章节补充 Y……"
- 不写"这里错了"，写"X 表述与 Y 不一致，建议……"
- 不堆套话；每条建议必须包含至少一处可定位的位置（章节号或页码）

**当某条审查需要更细节时**：除了主判的 chunk，可补读相邻 chunk；视觉问题（截图、图标）走步骤 6。骨架仅作为元信息（章节定位、页码）补充，不再作为主要判定来源——chunks 才是判定主入口。

### 步骤 6：软件工程图表规范性检查

工程型论文的用例图、系统架构图、ER 图、类图、流程图等是否符合 UML / 工程规范，是评审常考点之一。本步骤产出的所有问题计为"本步骤警告"，不计入红线，不影响步骤 4 的红线计数和步骤 8 的评议结论估计。

加载评估清单：

```
~/.claude/skills/nju-se-thesis-self-check/references/diagrams.md
```

#### 6.1 模型图像能力探针

**先确认模型能不能 Read 图像**——能力不足的模型直接跳过视觉评估，避免空跑。

```python
import fitz, os
PDF = "/path/to/paper.pdf"
TMP_DIR = os.environ["TMP_DIR"]   # 来自步骤 1 的 export；不要重新计算 tmp 顺延，会建一个空的新目录
FIGS_DIR = os.path.join(TMP_DIR, "figs")
os.makedirs(FIGS_DIR, exist_ok=True)

# 用 PyMuPDF 渲染论文第一页作为探针
doc = fitz.open(PDF)
probe_path = os.path.join(FIGS_DIR, "_probe.png")
pix = doc[0].get_pixmap(dpi=150)
pix.save(probe_path)
doc.close()
print(f"PROBE_PATH={probe_path}")
```

**接下来本 skill 的 Claude 用 Read 工具读这张 _probe.png**：

- 能 Read 成功并描述出页面内容 → `VISION_CAPABLE=true`，进入 6.2
- Read 报错（如"current model does not support image input"）或返回空 → `VISION_CAPABLE=false`，跳到 6.5 退化路径
- PyMuPDF 未安装 → 跳过整个步骤 6，在报告第六节写一行"PyMuPDF 未安装，请运行 `pip install pymupdf` 后重跑此步骤"，进入步骤 7

探针成功后**删除 _probe.png**（不污染 figs/ 子目录）。

#### 6.2 图注扫描

用 grep 在骨架上找所有图注，识别图所在页和图标题：

```bash
grep -nE "^图\s*[0-9]+[\-．.][0-9]+\s+\S+|^Figure\s+[0-9]+[\-．.][0-9]+\s+\S+" <skeleton>
```

骨架行格式形如 `[P.42] 图 3-2 系统架构图`，从中提取：
- `figure_id`：如 "3-2"
- `chapter`：3
- `page`：42
- `caption`：系统架构图

把所有图注存为列表 `figures = [{id, chapter, page, caption}, ...]`。

#### 6.3 整页渲染

**只渲染含图的页面**，不要全文渲染（80 页论文渲染慢且无意义）。

```python
import fitz, os
PDF = "/path/to/paper.pdf"
TMP_DIR = os.environ["TMP_DIR"]   # 来自步骤 1
FIGS_DIR = os.path.join(TMP_DIR, "figs")
os.makedirs(FIGS_DIR, exist_ok=True)

doc = fitz.open(PDF)
for fig in figures:
    page_idx = fig['page'] - 1  # 1-based → 0-based
    if 0 <= page_idx < len(doc):
        out = os.path.join(FIGS_DIR, f"page-{fig['page']:03d}.png")
        if not os.path.exists(out):  # 一页可能多图，避免重复渲染
            doc[page_idx].get_pixmap(dpi=150).save(out)
        fig['img_path'] = out
doc.close()
```

DPI 用 150（清晰度够辨识 UML 元素，体积可控）。

#### 6.4 分类与评估

对每张图：

1. **粗分类**：根据 `caption` 关键词初判类型
   - 含"用例" → use_case
   - 含"架构 / 体系结构 / 部署 / 拓扑" → architecture
   - 含"E-R / ER / 实体 / 表结构" → er
   - 含"类图 / Class" → class
   - 含"流程 / 活动 / Flow / Activity" → flowchart
   - 含"时序 / 顺序 / Sequence" → sequence
   - 含"状态 / State" → state
   - 其他 → unknown
2. **图像识别二次确认**：用 Read 工具读 `img_path`，让本 skill 的 Claude 直接看图判断
   - 类型与图注一致 → 用图注分类
   - 类型与图注不符（如图注写"系统架构"实际画的是流程图） → 记一条"图注与图内容不符"警告，按实际图类型评估
3. **按 references/diagrams.md 对应类别评估**：
   - 通用前置：图注、章内编号连续性、正文引用、清晰度
   - 类别专项：DGM-1 ~ DGM-6
4. **4+1 视图特别处理**：先用 grep 在骨架找 4+1 关键词；未命中则跳过 DGM-2，命中再走 DGM-2 流程

**输出格式**（每条问题）：

```yaml
- 图: 图3-2 系统架构图（P.42）
  类型: architecture（图注: 架构 → 实际: 用例图，类型不符）
  状态: ⚠️
  问题: actor 画成方框 / use case 画成菱形 / 缺 system boundary
  修改建议: 改用 stickman 表示 actor、椭圆表示 use case；为系统加矩形边界
```

合格的图只记一行 `- 图3-2 ✅`，不展开。

#### 6.5 关键图缺失检查

**仅工程型论文做此检查**。学术型跳过本小节。

按 references/diagrams.md 末尾"工程型论文的关键图缺失检查"的方法：用例图 / 系统架构图 / ER 或表结构图 至少应有两类。

完全缺 → 一条警告；缺一两类 → 对应警告。本检查即使 `VISION_CAPABLE=false` 也能做（基于图注关键词）。

#### 6.6 退化路径（VISION_CAPABLE=false）

模型不支持图像输入时：

1. 跳过 6.3 整页渲染、6.4 视觉评估
2. 仅做基于图注文本的检查：
   - 图注格式是否规范（"图 X-Y 标题"）
   - 章内图编号是否连续
   - 正文是否有"如图 X-Y 所示"的引用
   - 关键图是否缺失（基于图注关键词命中）
3. 在报告第六节顶部写明：

```
⚠️ 当前模型不支持图像输入，本节仅做基于图注文本的规范检查。
UML 图形元素（如 actor 是否画成 stickman、关系箭头方向是否正确等）建议人工抽查。
```

#### 6.7 收集结果

把本步骤产出的所有警告（无论来自视觉评估还是图注文本检查）暂存为 `diagram_warnings` 列表，供步骤 7 写入报告第六节。**本步骤的警告不计入步骤 5 的警告总数，不影响步骤 8 的评议结论估计**。

### 步骤 7：生成报告

按下面格式拼装报告。**不要在对话里贴完整报告**，写到磁盘。

**报告路径顺延**（与步骤 1 的 `$TMP_DIR` 同样规则，不覆盖前次产物；主报告与文风副报告**配套**顺延，下标一致）：

```bash
# 主报告
REPORT_PATH="$PAPER_DIR/${PAPER_TITLE}-review.md"
i=1
while [ -e "$REPORT_PATH" ]; do
  REPORT_PATH="$PAPER_DIR/${PAPER_TITLE}-review-$i.md"
  i=$((i+1))
done
echo "REPORT_PATH=$REPORT_PATH"   # 步骤 8、9 都用这个路径

# 文风副报告（与主报告共用同一下标，避免 review-2 配 style-5 这种错配）
suffix=$(echo "$REPORT_PATH" | sed -E "s|.*-review(-[0-9]+)?\.md|\1|")  # 取 -N 或空
STYLE_PATH="$PAPER_DIR/${PAPER_TITLE}-style${suffix}.md"
echo "STYLE_PATH=$STYLE_PATH"     # 步骤 9 写入文风+错别字详情用这个路径
```

命名约定：
- 首次：`<题目>-review.md` + `<题目>-style.md`（如步骤 9 跳过则不生成 style 文件）
- 第 N 次（N ≥ 1）：`<题目>-review-N.md` + `<题目>-style-N.md`

学生可以对照多次跑的差异，不会丢失上一轮反馈；文风检查结果较多放在副报告里，避免主报告过长冲淡核心结论。

#### 报告模板

```markdown
# 论文自检报告 — YYYY-MM-DD

**论文**：<paper.pdf 文件名>
**类别**：工程型 / 学术型（已确认）
**生成**：本报告由 nju-se-thesis-self-check skill 生成，仅供参考

---

## 一、首页摘要

| 项 | 数 |
|---|---|
| 🔴 致命问题（红线） | X |
| ⚠️ 警告 | Y |
| ✅ 通过 | Z |

**预估评议结论**：<不合格 / 修改后答辩 / 合格 / 良好>

> ⚠️ **免责声明**：本估计基于规则匹配，不能替代真人评审。真实评议结论取决于盲审专家的主观判断、所在批次整体水平、以及本 skill 没覆盖到的维度（如代码质量、Demo 可运行性等）。

### 必须先修的红线项

1. **[ENG-RED-2]** 文不对题（P.1 标题"智能"在第三、四章无对应实现）
   修改建议：……
2. ……

如果红线 = 0，写「✅ 无红线命中」。

---

## 二、🔴 红线条目（5 条）

[逐条展开]

---

## 三、学术质量（30 条）

按 ✅ → ⚠️ → ❌ 顺序排列，警告与不合格在前。

[逐条展开]

---

## 四、结构内容（11 条）

[逐条展开]

---

## 五、参考文献问题（5 条）

[逐条展开]

---

## 六、软件工程图表规范性（步骤 6 产出，不计入红线/警告总数）

> 本节由步骤 6 生成。**所有问题不计入第一节的"警告"统计、不影响预估评议结论**，仅供修改参考。
> 模型不支持图像输入时，本节仅含基于图注的文本检查；UML 图形元素的规范性请人工抽查。

### 6.1 检测能力
- 模型图像识别：✅ 支持 / ❌ 不支持（已退化到文本检查）
- 图注扫描：识别 N 张图，覆盖第 X-Y 章
- 整页渲染：`$TMP_DIR/figs/` 子目录（如已生成）

### 6.2 各图评估

按章节顺序列出。合格图只记一行 `图 X-Y ✅`；问题图按 `图 / 类型 / 问题 / 修改建议` 展开。

### 6.3 工程型关键图缺失（仅工程型）

如全部到位写「✅ 用例图 / 系统架构图 / ER 或表结构图 三类齐全」；缺失则逐条列出。

### 6.4 小结

- 图表警告：共 K 条
- 图类型分布：用例图 a / 架构图 b / ER 图 c / 类图 d / 流程图 e / 其他 f
- 修改优先级：先处理"图注与图内容不符""关系箭头方向错"等语义问题，再处理样式细节

---

## 七、修改 checklist（待勾选）

- [ ] [ENG-RED-2] 修改标题或在正文补充"智能"对应实现
- [ ] [ENG-A-04] 第二章"OpenTelemetry"在第四章未使用，二选一处理
- ...

<!-- 第八节由可选的步骤 9（humanizer-zh + 错别字检查）追加生成；如学生跳过该步骤则不出现 -->
```

#### 评议结论估计算法

按以下顺序判定（取首个匹配）：

| 条件 | 估计 |
|---|---|
| 红线 ≥ 1 | **不合格** 风险高 |
| 警告 ≥ 8 | **修改后答辩** |
| 警告 4-7 | **合格** |
| 警告 ≤ 3 且 通过 ≥ 45 | **良好** 或更高 |

### 步骤 8：对话输出摘要

只贴：
1. 报告路径
2. 红线项数 + 警告项数 + 通过数
3. 步骤 6 图表警告数（单独一行，注明"不计入红线/总警告，仅供修改参考"）
4. 预估评议结论
5. "必须先修的 X 项"列表（仅红线，逐条 1-2 行）
6. 一句话："详细分项及修改建议见报告 `<path>`"

不要在对话里贴 30 条以上的细节——刷屏会让学生看不到重点。

### 步骤 9（可选）：文风与错别字检查

步骤 8 输出摘要后，**主动**询问用户是否进行 AI 文风检查与错别字检查。这一步会跑 humanizer-zh（github.com/op7418/Humanizer-zh）+ 错别字扫描。

#### 9.1 询问用户

按以下文案询问（必须把开销讲清楚，让学生有预期）：

```
是否对全文做 AI 文风痕迹与错别字检查？（可选）

说明：
- 工具：humanizer-zh（按 24 种 AI 写作模式扫描）+ 错别字/标点检查
- 流程：复用步骤 3.2 已切好的 chunks，仅扫正文章节（chN.txt），逐块检查
- 论文当前 {pages} 页 / 正文约 {body_chars} 字（来自 chunks-index.json）/ 共 {N} 个正文 chunk，预估耗时 {M} 分钟，会消耗较多 token
- 结果会追加到已生成的报告：{report_path}

输入 y 进行检查；输入 n 跳过（不会影响已有报告）。
```

**AUTO_MODE**：不询问，默认进行；如检测到 humanizer-zh 未安装，则跳过文风部分但仍执行错别字检查，并在第八节顶部写明「未安装 humanizer-zh，本节仅含错别字检查；如需补充 AI 文风扫描请安装后重跑」。

`{pages}` 来自骨架元信息；`{body_chars}` 与 `{N}` 直接从 `$TMP_DIR/chunks/chunks-index.json` 的 `stats.body_chars` 与正文章节计数取值；`{M}` 按每块约 1-2 分钟估算并取整。

#### 9.2 检测 humanizer-zh 是否可用

```bash
ls ~/.claude/skills/humanizer-zh/SKILL.md 2>/dev/null && echo "INSTALLED" || echo "MISSING"
```

如未安装，**人工模式**告知用户并停在这里：

```
未检测到 humanizer-zh skill。请先安装：

  npx skills add https://github.com/op7418/Humanizer-zh.git

安装并重启 Agent 会话后再次运行论文自检即可。
```

不要尝试 fallback 到内置规则——humanizer-zh 的 24 类模式是它的核心资产，本 skill 不重复实现。

**AUTO_MODE** 下未安装时不停止：跳过文风部分，仅做错别字检查，在第八节顶部写明已跳过文风扫描及安装命令，让流程跑完。

#### 9.3 复用步骤 3.2 的切块

**默认复用**：如 `$TMP_DIR/chunks/chunks-index.json` 存在且 `stats.split_failed=false`，直接遍历 `chunks` 列表里所有 `id` 以 `ch` 开头的 chunk（即正文章节，跳过 cover-info / abstract-* / toc / acknowledgement / references / 等元素），把每个 `<chN>.txt` 作为一个待检查文本块。

如某章字符数 > 12000，可在内存中再按"节"切（按 `§X.1` / `§X.2` 标记拆段），但**不要把切分结果写回 chunks/**——避免污染步骤 3.2 的产物。

如 chunks 不存在或 `split_failed=true`（步骤 3.2 已降级），按下面的兜底切分：

- 用 `pdfplumber` 抽正文文本
- 跳过封面、致谢、目录、参考文献、附录等非正文页（用骨架元信息确定页码范围）
- 每章一块；单章 > 12000 字按节再切；单节 > 12000 字按段落切成 6000-10000 字
- 总块数控制在 5-12 块；过少合并，过多警示

#### 9.4 逐块检查

对每个文本块，**先错别字、后文风**两步做：

**(a) 错别字与标点检查**（由本 skill 的 Claude 直接读块文本判断，重点关注）：

- 同音字误用（"做/作"、"在/再"、"的/地/得"、"原/源"、"以/已"、"即/既"）
- 形近字（"末/未"、"己/已/巳"、"戊/戌/戍"、"撤/撒"、"暴/爆"）
- 专业术语前后写法不一致（"K8s / Kubernetes / k8s" 同一文中混用、"OpenTelemetry / Open-Telemetry" 等）
- 英文词中英标点错位（句号是 `.` 而段尾用了 `。`，或反之）
- 全角/半角混用（数字、字母、括号、引号）
- 引号成对错误（中文 `"` 配 `"`，英文 `"` 配 `"`，不要 `"` 配 `"`）
- 缺字、多字、重字（"的的"、"了了"、漏字时上下文不通）

每块产出列表：每条给 `原文片段 / 建议修正 / 章节定位`。

**(b) AI 文风检查**（调用 humanizer-zh skill）：

通过 Skill 工具调用：

```
Skill: humanizer-zh
args: 严格按你 SKILL.md 的 24 种 AI 模式扫描以下论文片段。
仅列出命中的模式，每条给出：模式编号+名称 / 原文片段（≤80 字）/ 建议改写 / 命中理由（一句话）。
不要改写整段，不要给概括性总评，只列条目。
来源：第 {chapter} 章，P.{p_start}-{p_end}

<文本块内容>
```

把每块的输出收集到内存中（标注其章节定位），不要在对话里逐块打印。

#### 9.5 写入独立的 style 副报告 + 在主报告里留指针

文风+错别字结果**不要**追加到主 review 报告里——条目可达数十条，会冲淡主报告核心结论。改为：

**(a) 独立写到 `$STYLE_PATH`**（步骤 7 已确定路径，与主报告共用下标）：

```markdown
# 文风与错别字检查 — YYYY-MM-DD

**论文**：<paper.pdf 文件名>
**配套主报告**：`<论文题目>-review.md`（或 -review-N.md）
**工具**：humanizer-zh + 内置错别字扫描
**切分**：复用步骤 3.2 的 N 个正文 chunk，覆盖 P.X-Y

---

## 一、错别字与标点问题

按章节列出。每条格式：

- **[第 X 章 P.YY]** 原文：「……」 → 建议：「……」 — 类型：同音字 / 形近字 / 标点 / 全半角 / 引号开关 / 术语不一致 / 重字漏字

如全文未发现，写「✅ 未发现明显错别字与标点问题」。

## 二、AI 文风痕迹（humanizer-zh 24 类模式）

### 2.1 命中频次表

按模式编号汇总，给一张统计表：模式编号 / 模式名 / 命中次数 / 重灾章节。

### 2.2 按章节展开

每章一节，列出该章命中的所有条目，每条格式：

- **[模式 N — 模式名]** P.YY：原文「……」 → 建议改写「……」（命中理由：……）

如某章未命中，写「✅ 本章未见明显 AI 写作痕迹」。

## 三、小结与修改建议优先级

- 错别字与标点问题：共 X 条
- AI 文风痕迹：共 Y 条（涉及 Z 类模式）
- 重灾区：列出 3-5 个最值得优先重写的位置
- 修改建议：先处理高频命中模式（≥3 次同一模式），再处理零散错别字

> ⚠️ humanizer-zh 与错别字扫描均为辅助工具，可能漏检或误报。本副报告条目较多并不直接等于论文质量差——AI 痕迹常集中在过渡句、本章小结、通用宣告等"低信息密度"区域；建议先做高频区域集中重写，再做全文标点统一。
```

**(b) 在主 review 报告里留指针段**——只追加一段简短摘要，告诉学生详细列表在 style 副报告里：

```markdown

---

## 八、文风与错别字检查（可选）

> 详细列表已写入独立副报告：`<论文题目>-style.md`（或 -style-N.md）
> 检查时间：YYYY-MM-DD

**统计**：
- 错别字与标点：共 X 条
- AI 文风痕迹：共 Y 条（涉及 Z 类模式）
- 命中前 3 类模式：模式 N1（K1 处）/ 模式 N2（K2 处）/ 模式 N3（K3 处）
- 重灾区：……（3-5 个最值得优先重写的位置）

详细条目（含原文片段+建议改写）请打开 `$STYLE_PATH`。
```

#### 9.6 对话输出

只贴：

1. 错别字 X 条 / 文风痕迹 Y 条
2. 命中前 3 的 humanizer-zh 模式（如"模式 10 三段式 8 处 / 模式 4 宣传性 7 处 / 模式 7 AI 词汇 5 处"）
3. 两句话：
   - "主报告第八节已加摘要指针：`$REPORT_PATH`"
   - "详细条目（含原文片段+建议改写）见副报告：`$STYLE_PATH`"

不要在对话里贴每一条原文片段——会刷屏。

## 红线触发后的特别提醒

报告顶部和对话里都要明确提醒：

> 🔴 命中 X 条红线。这些是评审会"一票否决"或"严重影响通过"的项，建议优先修改完毕后再处理其他警告项。

## 检查方法的复用

reference 文件中每条 checklist 均自带 `检查方法` 段（含 grep 模板、章节定位、模块名提取等），无需外部依赖；如发现多条重复的检查动作，可在本节后续补充统一模板。

