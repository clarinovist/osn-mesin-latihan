#!/usr/bin/env python3
"""Generate report.md from outline.yaml, fields.yaml and results/*.json."""
import json
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML required: pip install pyyaml")

BASE = Path(__file__).parent
OUTLINE_PATH = BASE / "outline.yaml"
FIELDS_PATH = BASE / "fields.yaml"

outline = yaml.safe_load(OUTLINE_PATH.read_text())
fields_def = yaml.safe_load(FIELDS_PATH.read_text())

topic = outline.get("topic", "Research Report")
research_question = outline.get("research_question", "")
output_dir = BASE / outline.get("execution", {}).get("output_dir", "./results")
items = outline.get("items", [])

CATEGORY_MAPPING = {
    "Basic Info": ["basic_info", "Basic Info"],
    "Diagnosis Capability": ["diagnosis_capability", "Diagnosis Capability"],
    "Parent Role": ["parent_role", "Parent Role"],
    "Evidence & Market Signal": ["evidence_market_signal", "Evidence & Market Signal"],
    "Sources": ["sources", "Sources"],
}

NESTED_TOP_KEYS = set()
for keys in CATEGORY_MAPPING.values():
    NESTED_TOP_KEYS.update(keys)

INTERNAL_FIELDS = {"_source_file", "uncertain"}


def slugify(name):
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def json_slug(item_name):
    s = re.sub(r"[^\w\s]", "", item_name)
    s = re.sub(r"\s+", "_", s.strip())
    return s


STOPWORDS = {
    "riset", "untuk", "dan", "yang", "di", "ke", "dari", "the", "of", "for",
    "a", "an", "&", "konteks", "sinyal", "pasar", "makro",
}


def word_set(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 1}


def assign_result_files(items_list):
    candidates = list(output_dir.glob("*.json"))
    slug_map = {c.stem: c for c in candidates}
    assigned = {}
    used = set()

    remaining_items = []
    for item in items_list:
        name = item.get("name", "")
        slug = json_slug(name)
        if slug in slug_map:
            assigned[name] = slug_map[slug]
            used.add(slug_map[slug])
        else:
            remaining_items.append(item)

    unused = [c for c in candidates if c not in used]
    for item in remaining_items:
        name = item.get("name", "")
        target_words = word_set(name)
        best, best_score = None, 0
        for c in unused:
            score = len(target_words & word_set(c.stem))
            if score > best_score:
                best, best_score = c, score
        if best is not None and best_score > 0:
            assigned[name] = best
            unused.remove(best)

    return assigned


RESULT_FILE_MAP = assign_result_files(items)


def find_result_file(item_name):
    return RESULT_FILE_MAP.get(item_name)


def is_uncertain(value):
    if value is None:
        return True
    if isinstance(value, str):
        if value.strip() == "":
            return True
        if "[uncertain]" in value:
            return True
    return False


def get_field_value(data, field_name):
    if field_name in data:
        return data[field_name]
    for cat_keys in CATEGORY_MAPPING.values():
        for ck in cat_keys:
            sub = data.get(ck)
            if isinstance(sub, dict) and field_name in sub:
                return sub[field_name]
    for v in data.values():
        if isinstance(v, dict) and field_name in v:
            return v[field_name]
    return None


def format_value(value):
    if isinstance(value, list):
        if not value:
            return ""
        if all(isinstance(x, dict) for x in value):
            lines = []
            for d in value:
                lines.append(" | ".join(f"{k}: {v}" for k, v in d.items()))
            return "\n".join(f"- {l}" for l in lines)
        if all(isinstance(x, str) for x in value):
            joined = ", ".join(value)
            if len(joined) <= 100:
                return joined
            return "\n".join(f"- {x}" for x in value)
        return "\n".join(f"- {x}" for x in value)
    if isinstance(value, dict):
        return "\n".join(f"- **{k}**: {v}" for k, v in value.items())
    text = str(value)
    if len(text) > 100:
        return f"> {text}"
    return text


def short_first_clause(value, max_len=40):
    if not isinstance(value, str):
        return str(value)
    for sep in [" - ", " — ", ". ", "\n"]:
        if sep in value:
            value = value.split(sep, 1)[0]
            break
    value = value.strip()
    if len(value) > max_len:
        value = value[:max_len].rstrip() + "…"
    return value


TOC_FIELDS = ["category", "does_error_type_diagnosis"]
TOC_LABELS = {"category": "Kategori", "does_error_type_diagnosis": "Diagnosis Jenis Kesalahan"}

loaded_items = []
for item in items:
    name = item.get("name", "")
    result_file = find_result_file(name)
    if result_file is None:
        loaded_items.append({"item": item, "data": None, "uncertain_list": [], "anchor": slugify(name)})
        continue
    data = json.loads(result_file.read_text())
    uncertain_list = data.get("uncertain", []) or []
    loaded_items.append({
        "item": item,
        "data": data,
        "uncertain_list": uncertain_list,
        "anchor": slugify(name),
    })

lines = []
lines.append(f"# {topic}\n")
if research_question:
    lines.append(f"**Pertanyaan Riset:** {research_question.strip()}\n")
lines.append(f"**Total item:** {len(items)} | **Selesai:** {sum(1 for x in loaded_items if x['data'])}\n")

lines.append("## Daftar Isi\n")
for i, entry in enumerate(loaded_items, 1):
    name = entry["item"].get("name", "")
    anchor = entry["anchor"]
    data = entry["data"]
    if data is None:
        lines.append(f"{i}. {name} *(belum ada hasil)*")
        continue
    summary_parts = []
    for f in TOC_FIELDS:
        val = get_field_value(data, f)
        if is_uncertain(val) or (entry["uncertain_list"] and f in entry["uncertain_list"]):
            continue
        if val:
            summary_parts.append(f"{TOC_LABELS.get(f, f)}: {short_first_clause(val)}")
    summary = " | ".join(summary_parts)
    line = f"{i}. [{name}](#{anchor})"
    if summary:
        line += f" - {summary}"
    lines.append(line)
lines.append("")

lines.append("## Detail per Item\n")
for entry in loaded_items:
    item = entry["item"]
    name = item.get("name", "")
    data = entry["data"]
    anchor = entry["anchor"]
    lines.append(f"### {name}\n")
    lines.append(f'<a id="{anchor}"></a>')
    if data is None:
        lines.append("*Belum ada hasil riset untuk item ini.*\n")
        continue
    uncertain_list = set(entry["uncertain_list"])
    extra_fields = {}
    consumed = set()

    for category_block in fields_def.get("field_categories", []):
        cat_name = category_block.get("category", "")
        cat_fields = category_block.get("fields", [])
        rows = []
        for f in cat_fields:
            fname = f.get("name")
            consumed.add(fname)
            if fname in uncertain_list:
                continue
            val = get_field_value(data, fname)
            if is_uncertain(val):
                continue
            rows.append((fname, format_value(val)))
        if rows:
            lines.append(f"**{cat_name}**\n")
            for fname, val in rows:
                if "\n" in val:
                    lines.append(f"- **{fname}**:\n{val}")
                else:
                    lines.append(f"- **{fname}**: {val}")
            lines.append("")

    for k, v in data.items():
        if k in INTERNAL_FIELDS or k in consumed or k in NESTED_TOP_KEYS:
            continue
        if k in uncertain_list:
            continue
        if is_uncertain(v):
            continue
        extra_fields[k] = v

    if extra_fields:
        lines.append("**Info Tambahan**\n")
        for k, v in extra_fields.items():
            val = format_value(v)
            if "\n" in val:
                lines.append(f"- **{k}**:\n{val}")
            else:
                lines.append(f"- **{k}**: {val}")
        lines.append("")

    if uncertain_list:
        lines.append("**Field dengan nilai uncertain (di-skip):**")
        for u in sorted(uncertain_list):
            lines.append(f"- {u}")
        lines.append("")

report = "\n".join(lines)
(BASE / "report.md").write_text(report)
print(f"Report written to {BASE / 'report.md'} ({len(report)} chars, {len(loaded_items)} items)")
