"""按 SKILL.md 步骤 3.5 切块需求，把 PDF 全文按"范围"切成独立 .txt 文件。

输入：论文 PDF。
输出：
  <out_dir>/cover-info.txt
  <out_dir>/abstract-cn.txt
  <out_dir>/abstract-en.txt
  <out_dir>/toc.txt（如能识别）
  <out_dir>/ch1.txt ... <out_dir>/chN.txt
  <out_dir>/acknowledgement.txt（如能识别）
  <out_dir>/references.txt
  <out_dir>/chunks-index.json

chunks-index.json 字段：
  {
    "chunks": [{"id": "ch3", "file": "ch3.txt", "title": "...", "pages": [31, 47], "chars": 18923}, ...],
    "range_map": {
       "last-ch": ["ch6"],
       "ch3-end": ["ch3", "ch4", "ch5", "ch6"],
       "all-body": ["ch1", ..., "ch6"],
       "design-impl": ["ch3", "ch4", "ch5"],
       "test-ch": ["ch5"],
       "methods-ch": ["ch3"],
       "experiment-ch": ["ch4"]
    },
    "stats": {"total_chars": 123456, "body_chars": 109321, "split_failed": false}
  }

设计原则：
- 复用 extract_skeleton.py 中的 split_chapters / extract_abstracts 逻辑
- 章节边界识别失败（split_chapters 退化）→ 仅写 cover-info / 摘要 / references / chunks-index.json
  并把 stats.split_failed 置为 true，让 SKILL.md 主流程降级到骨架模式
- 单章超过 20000 字仅警告，不主动再切（让评审 prompt 自己处理；过度细分会破坏章内
  连贯论证的判断）
"""
import argparse
import json
import re
import sys
from pathlib import Path

# 复用 extract_skeleton 的核心解析
sys.path.insert(0, str(Path(__file__).parent))
from extract_skeleton import (
    extract_pages,
    split_chapters,
    extract_abstracts,
)

# 致谢章识别：独占行的「致 谢」/「Acknowledgement」
ACK_HEADER = re.compile(r'^\s*(致\s*谢|致谢|Acknowledg(e?ments?|ement))\s*$', re.IGNORECASE)
# 参考文献章识别
REF_HEADER = re.compile(r'^\s*参\s*考\s*文\s*献\s*$|^\s*References?\s*$', re.IGNORECASE)
# 目录识别
TOC_HEADER = re.compile(r'^\s*目\s*录\s*$|^\s*Contents?\s*$', re.IGNORECASE)
# 第一章识别（用于目录截止）
CH1_HEADER = re.compile(r'^第[一1]\s*章\b')

# 动态范围关键词
DESIGN_IMPL_KW = ['需求', '分析', '架构', '设计', '实现', '系统']
TEST_CH_KW = ['测试', '评估', 'Test', '验证']
METHODS_CH_KW = ['方法', '模型', '算法', '形式化', '问题描述']
EXPERIMENT_CH_KW = ['实验', '评估', 'Experiment', '消融', '对比']


def find_first_page_with(pages: list[dict], pattern: re.Pattern) -> int | None:
    """返回首个匹配 pattern（独占行）的页码（1-based），未找到返回 None。"""
    for p in pages:
        for line in p['text'].split('\n'):
            if pattern.match(line.strip()):
                return p['page_no']
    return None


def find_last_page_with(pages: list[dict], pattern: re.Pattern) -> int | None:
    """返回最末出现匹配 pattern 的页码（用于参考文献）。"""
    last = None
    for p in pages:
        for line in p['text'].split('\n'):
            if pattern.match(line.strip()):
                last = p['page_no']
                break
    return last


def slice_pages_text(pages: list[dict], start: int, end: int) -> str:
    """取 [start, end] 闭区间所有页文本拼接。"""
    return '\n'.join(p['text'] for p in pages if start <= p['page_no'] <= end)


def classify_chapter_ranges(chapters: list[dict]) -> dict[str, list[str]]:
    """根据章标题关键词把章节归到 design-impl / test-ch / methods-ch / experiment-ch。"""
    ranges = {
        'design-impl': [],
        'test-ch': [],
        'methods-ch': [],
        'experiment-ch': [],
    }
    for i, c in enumerate(chapters, 1):
        title = c['title']
        chid = f'ch{i}'
        if any(kw in title for kw in DESIGN_IMPL_KW):
            ranges['design-impl'].append(chid)
        if any(kw in title for kw in TEST_CH_KW):
            ranges['test-ch'].append(chid)
        if any(kw in title for kw in METHODS_CH_KW):
            ranges['methods-ch'].append(chid)
        if any(kw in title for kw in EXPERIMENT_CH_KW):
            ranges['experiment-ch'].append(chid)
    return ranges


def write_chunk(out_dir: Path, name: str, text: str) -> dict | None:
    """写一个 chunk 文件；空文本不写入，返回 None。"""
    text = text.strip()
    if not text:
        return None
    fp = out_dir / f'{name}.txt'
    fp.write_text(text, encoding='utf-8')
    return {'id': name, 'file': fp.name, 'chars': len(text)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf', help='论文 PDF 路径')
    ap.add_argument('--out', required=True, help='chunks 输出目录（建议 <paper_dir>/tmp/chunks）')
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    pages = extract_pages(args.pdf)
    chapters = split_chapters(pages)
    cn_abs, en_abs = extract_abstracts(pages)

    chunks_meta: list[dict] = []

    # === 固定范围 ===
    # 封面：仅第 1 页文本
    if pages:
        m = write_chunk(out_dir, 'cover-info', pages[0]['text'])
        if m:
            m.update(title='封面', pages=[1])
            chunks_meta.append(m)

    if cn_abs:
        m = write_chunk(out_dir, 'abstract-cn', cn_abs)
        if m:
            m.update(title='中文摘要')
            chunks_meta.append(m)

    if en_abs:
        m = write_chunk(out_dir, 'abstract-en', en_abs)
        if m:
            m.update(title='英文摘要')
            chunks_meta.append(m)

    # 目录：从首个 "目录" 行所在页到第一章首页前一页
    toc_start = find_first_page_with(pages, TOC_HEADER)
    ch1_start = find_first_page_with(pages, CH1_HEADER)
    if toc_start and ch1_start and toc_start < ch1_start:
        text = slice_pages_text(pages, toc_start, ch1_start - 1)
        m = write_chunk(out_dir, 'toc', text)
        if m:
            m.update(title='目录', pages=[toc_start, ch1_start - 1])
            chunks_meta.append(m)

    # 致谢：从首个 "致谢" 行所在页到下一段（参考文献前）
    ack_start = find_first_page_with(pages, ACK_HEADER)
    # 参考文献：首次出现 "参考文献" 独占行的页（不要用 last——很多 NJU 论文页眉每页都有，
    # last 会退化到最后一页）
    ref_start = find_first_page_with(pages, REF_HEADER)
    if ack_start:
        ack_end = (ref_start - 1) if (ref_start and ref_start > ack_start) else pages[-1]['page_no']
        text = slice_pages_text(pages, ack_start, ack_end)
        m = write_chunk(out_dir, 'acknowledgement', text)
        if m:
            m.update(title='致谢', pages=[ack_start, ack_end])
            chunks_meta.append(m)

    # 参考文献：从最末 "参考文献" 行所在页到末尾
    if ref_start:
        text = slice_pages_text(pages, ref_start, pages[-1]['page_no'])
        m = write_chunk(out_dir, 'references', text)
        if m:
            m.update(title='参考文献', pages=[ref_start, pages[-1]['page_no']])
            chunks_meta.append(m)

    # === 各章 ===
    split_failed = False
    body_chars = 0
    if chapters and not chapters[0]['title'].startswith('(未识别章节'):
        for i, c in enumerate(chapters, 1):
            chid = f'ch{i}'
            m = write_chunk(out_dir, chid, c['text'])
            if m:
                m.update(title=c['title'], pages=[c['page_start'], c['page_end']])
                chunks_meta.append(m)
                body_chars += m['chars']
    else:
        split_failed = True

    # === 动态范围映射 ===
    chapter_ids = [c['id'] for c in chunks_meta if c['id'].startswith('ch') and c['id'][2:].isdigit()]
    range_map: dict[str, list[str]] = {
        'all-body': chapter_ids,
        'last-ch': [chapter_ids[-1]] if chapter_ids else [],
        'ch3-end': [c for c in chapter_ids if int(c[2:]) >= 3],
    }
    range_map.update(classify_chapter_ranges(chapters) if not split_failed else {
        'design-impl': [],
        'test-ch': [],
        'methods-ch': [],
        'experiment-ch': [],
    })

    # === 索引 ===
    total_chars = sum(c['chars'] for c in chunks_meta)
    index = {
        'chunks': chunks_meta,
        'range_map': range_map,
        'stats': {
            'total_chars': total_chars,
            'body_chars': body_chars,
            'chapter_count': len(chapter_ids),
            'split_failed': split_failed,
        },
    }
    (out_dir / 'chunks-index.json').write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    print(f'wrote {len(chunks_meta)} chunks to {out_dir}')
    print(f'  body_chars={body_chars}  chapter_count={len(chapter_ids)}  split_failed={split_failed}')
    if split_failed:
        print('  WARN: 章节切分退化，主流程应降级到 skeleton-only 模式', file=sys.stderr)


if __name__ == '__main__':
    main()
