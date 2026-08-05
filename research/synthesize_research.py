#!/usr/bin/env python3
"""
Synthesizes raw research articles into book chapter notes + evidence map.
Run after fetch_news.py to process new articles.

Pipeline:
  1. Scan sources/new/ for unprocessed JSON articles
  2. Classify each article by book chapter (keyword matching)
  3. Extract key facts, quotes, named entities
  4. Append to chapter-specific notes files
  5. Update the evidence map
  6. Produce a weekly digest
"""
import os
import json
import re
import hashlib
from datetime import datetime
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
SOURCES_NEW = PROJECT_ROOT / "sources" / "new"
CHAPTER_NOTES = PROJECT_ROOT / "writing" / "notes"
EVIDENCE_MAP = PROJECT_ROOT / "research" / "evidence_map.md"
DIGEST_DIR = PROJECT_ROOT / "research" / "digests"
PROCESSED_LOG = PROJECT_ROOT / "research" / "processed_articles.json"

CHAPTER_NOTES.mkdir(parents=True, exist_ok=True)
DIGEST_DIR.mkdir(parents=True, exist_ok=True)

# Chapter classification rules: loaded from chapters.json
CHAPTER_RULES = []
CHAPTERS_FILE = PROJECT_ROOT / "research" / "chapters.json"
if CHAPTERS_FILE.exists():
    try:
        raw = json.loads(CHAPTERS_FILE.read_text())
        CHAPTER_RULES = [(c[0], c[1], [k.lower() for k in c[2]]) for c in raw]
    except: pass

def load_processed():
    if PROCESSED_LOG.exists():
        with open(PROCESSED_LOG) as f:
            return set(json.load(f))
    return set()

def save_processed(processed):
    with open(PROCESSED_LOG, 'w') as f:
        json.dump(list(processed), f, indent=2)

def classify_article(title, snippet):
    """Return list of (chapter_num, chapter_title) matches."""
    text = (title + " " + snippet).lower()
    matches = []
    for ch_num, ch_title, keywords in CHAPTER_RULES:
        for kw in keywords:
            if kw in text:
                matches.append((ch_num, ch_title))
                break
    return matches

def strip_html(s):
    return re.sub(r'<[^>]+>', '', s).replace('&amp;', '&').replace('&nbsp;', ' ')

def extract_entities(text):
    text = strip_html(text)
    entities = {
        "people": set(),
        "orgs": set(),
        "amounts": set(),
    }

    KNOWN_PEOPLE = {
        "Andrew Yates", "Eileen Hoggett", "Martin Sheppard", "Suzanne Bell",
        "Louise Capon", "Dorothy Hisgrove", "Deborah O'Neill", "David Pocock",
        "Brendan Lyon", "Geoffrey Baird", "Anthony Whealy", "Rob Rogers",
        "Ross McPherson", "Sarah Court", "Mike Scott", "Dylan Hoskins",
        "Chris Foster", "Doug Ferguson",
    }
    for name in KNOWN_PEOPLE:
        if name.lower() in text.lower():
            entities["people"].add(name)

    # Dollar amounts
    amounts = re.findall(r'\$[\d,]+(?:\.\d+)?[mb]?', text)
    entities["amounts"].update(amounts)

    # Key orgs
    for org in ["KPMG", "PwC", "EY", "Deloitte", "ASIC", "Lendlease", "NAB", "RBA",
                 "ASX", "Capgemini", "CAANZ", "Treasury", "Finance", "ATO"]:
        if org.lower() in text:
            entities["orgs"].add(org)

    return entities

def extract_facts(title, snippet, text):
    """Extract notable facts from the article."""
    text = strip_html(text)
    facts = []

    claim_patterns = [
        (r'alleged\s+(that\s+)?([^.]{20,200})', "Allegation"),
        (r'admitted\s+(that\s+)?([^.]{20,100})', "Admission"),
        (r'(confirmed|revealed|disclosed)\s+(that\s+)?([^.]{20,200})', "Disclosure"),
        (r'resigned|stepped\s+down|demoted|sacked|fired\s+([^.]{20,150})', "Personnel change"),
        (r'investigat(ion|e|es|ed)\s+([^.]{20,200})', "Investigation"),
    ]

    for pattern, label in claim_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches[:2]:
            m_list = m if isinstance(m, tuple) else (m,)
            claim = next((g.strip() for g in reversed(m_list) if g.strip()), "")
            if len(claim) > 30:
                facts.append(f"[{label}] {claim}")

    return facts[:5]

def sanitize_filename(s):
    s = s.lower().replace(' ', '_')
    s = re.sub(r'[\\/*?:"<>|/]', '', s)
    return s[:30]

def write_chapter_note(ch_num, ch_title, article, entities, facts):
    """Append research findings to chapter-specific notes file."""
    note_file = CHAPTER_NOTES / f"ch{ch_num:02d}_{sanitize_filename(ch_title)}.md"
    
    entry = f"""
## {article.get('date', 'Date unknown')} — {article['title']}
**Source**: {article['url']}
**Fetched**: {article.get('fetched_at', '')}

{facts[0] if facts else ''}

"""
    # Entities
    if entities["people"] or entities["orgs"]:
        entry += "**Mentions**: "
        parts = []
        if entities["people"]: parts.append(f"People: {', '.join(sorted(entities['people'])[:5])}")
        if entities["orgs"]: parts.append(f"Orgs: {', '.join(sorted(entities['orgs']))}")
        entry += "; ".join(parts) + "\n"

    entry += "\n---\n"

    with open(note_file, 'a', encoding='utf-8') as f:
        f.write(entry)

def update_evidence_map(ch_num, ch_title, article, entities, facts):
    """Update the evidence map document."""
    if not EVIDENCE_MAP.exists():
        with open(EVIDENCE_MAP, 'w', encoding='utf-8') as f:
            f.write("# KPMG Book — Evidence Map\n\n")
            f.write("Maps every claim to its source(s). Updated automatically by synthesize_research.py.\n\n")
            f.write("---\n\n")

    entry = f"### [{article['title']}]({article['url']})\n"
    entry += f"**Chapter**: {ch_num}. {ch_title}  \n"
    entry += f"**Date**: {article.get('date', '')}  \n"
    entry += f"**Source**: {article['url']}  \n"
    if facts:
        entry += f"**Facts**:\n"
        for f in facts[:3]:
            entry += f"- {f}\n"
    entry += "\n"

    with open(EVIDENCE_MAP, 'a', encoding='utf-8') as f:
        f.write(entry)

def write_weekly_digest(new_articles_by_chapter, date_str):
    """Write a weekly research digest."""
    digest_file = DIGEST_DIR / f"digest_{date_str}.md"
    
    with open(digest_file, 'w', encoding='utf-8') as f:
        f.write(f"# Weekly Research Digest — {date_str}\n\n")
        f.write(f"**Total new articles processed**: {sum(len(v) for v in new_articles_by_chapter.values())}\n\n")
        
        for ch_num in sorted(new_articles_by_chapter.keys()):
            articles = new_articles_by_chapter[ch_num]
            if not articles:
                continue
            ch_title = articles[0][2]  # chapter title
            f.write(f"## Chapter {ch_num}: {ch_title}\n\n")
            for title, url, _, date in articles:
                f.write(f"- [{title}]({url}) — *{date}*\n")
            f.write("\n")
    
    print(f"  Digest written: {digest_file}")
    return digest_file

def main():
    print(f"[{datetime.now()}] Starting research synthesis...")
    
    processed = load_processed()
    new_count = 0
    new_by_chapter = defaultdict(list)
    
    # Scan for new JSON articles
    for fpath in sorted(SOURCES_NEW.glob("*.json")):
        article_id = fpath.stem
        if article_id in processed:
            continue
        
        try:
            with open(fpath) as f:
                article = json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            print(f"  Skipping bad JSON: {fpath.name} — {e}")
            continue
        
        title = article.get("title", "Untitled")
        snippet = article.get("snippet", article.get("description", ""))
        url = article.get("url", "")
        pub_date = article.get("date", "")
        
        # Classify
        matches = classify_article(title, snippet)
        if not matches:
            matches = [(0, "General / Unclassified")]
        
        # Extract
        full_text = title + " " + snippet
        entities = extract_entities(full_text)
        facts = extract_facts(title, snippet, full_text)
        
        # Write to chapter notes
        for ch_num, ch_title in matches:
            write_chapter_note(ch_num, ch_title, article, entities, facts)
            
            # Add to evidence map (only primary chapter, skip general)
            if ch_num == matches[0][0] and ch_num > 0:
                update_evidence_map(ch_num, ch_title, article, entities, facts)
            
            new_by_chapter[ch_num].append((title, url, ch_title, pub_date))
        
        new_count += 1
        processed.add(article_id)
    
    # Write digest if we found anything new
    if new_count > 0:
        date_str = datetime.now().strftime("%Y-%m-%d")
        digest_file = write_weekly_digest(new_by_chapter, date_str)
        save_processed(sorted(processed))
        print(f"[{datetime.now()}] Processed {new_count} new articles")
        print(f"  Summary: {digest_file}")
    else:
        print(f"[{datetime.now()}] No new articles to process")
    
    # Show current chapter note stats
    print("")
    print("Chapter notes files:")
    for f in sorted(CHAPTER_NOTES.glob("*.md")):
        line_count = len(f.read_text().strip().split('\n'))
        print(f"  {f.name}: {line_count} lines")

if __name__ == "__main__":
    main()