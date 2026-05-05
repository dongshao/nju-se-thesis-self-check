import pdfplumber
import re
from pathlib import Path

CHAPTER_PATTERN = re.compile(r'^第[一二三四五六七八九十]+章\s*\S*')


def split_chapters(pages: list[dict]) -> list[dict]:
    """按 '第X章' 切章节。返回 [{'title': str, 'page_start': int, 'page_end': int, 'text': str}, ...]"""
    markers = []  # [(page_no, title)]
    for p in pages:
        for line in p['text'].split('\n'):
            line = line.strip()
            m = CHAPTER_PATTERN.match(line)
            if m:
                markers.append((p['page_no'], line))
                break  # 一页只算第一个章节标记

    if not markers:
        # 退化策略：按页均分 5 段
        n = max(1, len(pages) // 5)
        chapters = []
        for i in range(0, len(pages), n):
            chunk = pages[i:i+n]
            chapters.append({
                'title': f'(未识别章节 — 退化按页码均分) 段 {i//n + 1}',
                'page_start': chunk[0]['page_no'],
                'page_end': chunk[-1]['page_no'],
                'text': '\n'.join(p['text'] for p in chunk),
            })
        return chapters

    # 正常切分
    chapters = []
    for i, (start_page, title) in enumerate(markers):
        end_page = markers[i+1][0] - 1 if i+1 < len(markers) else pages[-1]['page_no']
        text = '\n'.join(p['text'] for p in pages if start_page <= p['page_no'] <= end_page)
        chapters.append({
            'title': title,
            'page_start': start_page,
            'page_end': end_page,
            'text': text,
        })
    return chapters


SIGNAL_WORDS = ['本文', '本系统', '提出', '设计了', '实现了', '采用', '基于', '相比', '实验表明', '结果表明', '本章', '架构', '主要']
SECTION_PATTERN = re.compile(r'^(\d+(?:\.\d+)*)\s+(\S+)')


def extract_key_sentences(chapter: dict) -> list[dict]:
    """从一章里抽 3-8 条关键句。返回 [{'page_no': int, 'section': str, 'text': str}, ...]"""
    text = chapter['text']
    current_section = chapter['title']
    candidates = []  # (score, section, text)
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        sm = SECTION_PATTERN.match(line)
        if sm:
            current_section = f"§{sm.group(1)} {sm.group(2)}"
            continue
        # 按中文句号 / 句号切
        for sent in re.split(r'[。！？]', line):
            sent = sent.strip()
            if 5 <= len(sent) <= 200:
                score = sum(1 for w in SIGNAL_WORDS if w in sent)
                candidates.append((score, current_section, sent))

    # 按 score 降序、length 升序排，取前 8
    candidates.sort(key=lambda x: (-x[0], len(x[2])))
    top = candidates[:8]
    # page_no 简化为章首页
    return [{'page_no': chapter['page_start'], 'section': sec, 'text': sent} for _, sec, sent in top]


def extract_pages(pdf_path: Path | str) -> list[dict]:
    """从 PDF 提取每页文本，返回 [{'page_no': int, 'text': str}, ...]"""
    pages = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, p in enumerate(pdf.pages, 1):
            pages.append({'page_no': i, 'text': p.extract_text() or ''})
    return pages


TITLE_PATTERN = re.compile(r'^.*(?:系统|平台|框架|算法|方法|引擎|工具).*(?:的)?(?:设计与实现|研究与实现|研究|实现|设计)\s*$')


def extract_title(pages: list[dict], fallback_filename: str) -> str:
    """从前 3 页找形如《XX 系统的设计与实现》的标题行。失败回退到文件名（去 .pdf 后缀）"""
    for p in pages[:3]:
        for line in p['text'].split('\n'):
            line = line.strip()
            if 6 <= len(line) <= 50 and TITLE_PATTERN.match(line):
                return line
    return Path(fallback_filename).stem


def extract_metadata(pages: list[dict]) -> dict:
    """提取论文元信息"""
    full_text = '\n'.join(p['text'] for p in pages)

    # 测试章 / 实验对比章
    # 追加「系统实现与测试」以匹配该章名完整字面量（「系统测试」是子串但中间有「实现与」隔断）
    has_test = any(kw in full_text for kw in ['系统测试', '本章测试', '测试用例', '压测', '性能测试', '系统实现与测试'])
    has_exp = any(kw in full_text for kw in ['实验设计', '实验结果', 'baseline', '消融', '对比实验'])

    # 参考文献区段（找最末出现的「参考文献」标题之后的内容）
    ref_idx = full_text.rfind('参考文献')
    ref_section = full_text[ref_idx:] if ref_idx >= 0 else ''
    # 粗判：以 [N] 或 N. 开头的行
    ref_lines = re.findall(r'(?:^|\n)\s*(?:\[\d+\]|\d+\.)\s', ref_section)
    ref_count = len(ref_lines)

    # GitHub / StackOverflow / 百度百科 链接数
    github_count = len(re.findall(r'github\.com|stackoverflow\.com|baike\.baidu\.com', full_text, re.IGNORECASE))

    return {
        'total_pages': len(pages),
        'has_test_chapter': has_test,
        'has_experiment_chapter': has_exp,
        'ref_count': ref_count,
        'github_link_count': github_count,
    }


def build_skeleton_md(pdf_path: Path, pages: list[dict], chapters: list[dict], meta: dict, title: str) -> str:
    """拼装骨架 md"""
    lines = [
        '# 论文元信息',
        f'- 标题: {title}',
        f'- 总页数: {meta["total_pages"]}',
        f'- 章节数: {len(chapters)}',
        f'- 是否有"系统测试"章: {"是" if meta["has_test_chapter"] else "否"}',
        f'- 是否有"实验对比/baseline"章: {"是" if meta["has_experiment_chapter"] else "否"}',
        f'- 参考文献数: {meta["ref_count"]}',
        f'- 参考文献中含 GitHub/StackOverflow 链接数: {meta["github_link_count"]}',
        '',
        '## 摘要',
    ]
    # 摘要：取前 3 页中含「摘要」关键词的段落
    abstract = ''
    for p in pages[:3]:
        if '摘要' in p['text']:
            abstract = p['text']
            break
    lines.append('> ' + abstract.replace('\n', '\n> '))
    lines += ['', '## 目录树']
    for c in chapters:
        lines.append(f"- {c['title']} (p.{c['page_start']}-{c['page_end']})")
    lines += ['', '## 各章关键句索引']
    for c in chapters:
        lines.append(f"### {c['title']} (p.{c['page_start']}-{c['page_end']})")
        for s in extract_key_sentences(c):
            lines.append(f"- {s['section']} [p.{s['page_no']}]: \"{s['text']}\"")
        lines.append('')
    return '\n'.join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('pdf', help='论文 PDF 路径')
    parser.add_argument('--out', required=True, help='骨架 md 输出路径')
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    pages = extract_pages(pdf_path)
    chapters = split_chapters(pages)
    meta = extract_metadata(pages)
    title = extract_title(pages, fallback_filename=pdf_path.name)
    md = build_skeleton_md(pdf_path, pages, chapters, meta, title)
    Path(args.out).write_text(md, encoding='utf-8')
    print(f'wrote {args.out} ({len(md)} chars, title={title})')


if __name__ == '__main__':
    main()
