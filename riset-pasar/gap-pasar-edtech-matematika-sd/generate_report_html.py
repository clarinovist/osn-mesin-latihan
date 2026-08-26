#!/usr/bin/env python3
"""Generate a self-contained styled report.html from outline.yaml, fields.yaml, results/*.json."""
import json
import re
from pathlib import Path
from html import escape

import yaml

BASE = Path(__file__).parent
outline = yaml.safe_load((BASE / "outline.yaml").read_text())
fields_def = yaml.safe_load((BASE / "fields.yaml").read_text())

topic = outline["topic"]
research_question = outline["research_question"].strip()
output_dir = BASE / outline.get("execution", {}).get("output_dir", "./results")
items = outline["items"]

CATEGORY_LABELS = {
    "competitor_product": "Produk Kompetitor",
    "diagnostic_benchmark": "Benchmark Diagnostik",
    "academic_framework": "Kerangka Akademik",
    "market_signal": "Sinyal Pasar",
}
CATEGORY_ORDER = ["competitor_product", "diagnostic_benchmark", "academic_framework", "market_signal"]

STOPWORDS = {"riset", "untuk", "dan", "yang", "di", "ke", "dari", "the", "of", "for", "a", "an", "&", "konteks", "sinyal", "pasar", "makro"}


def word_set(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 1}


def json_slug(name):
    s = re.sub(r"[^\w\s]", "", name)
    return re.sub(r"\s+", "_", s.strip())


def assign_result_files():
    candidates = list(output_dir.glob("*.json"))
    slug_map = {c.stem: c for c in candidates}
    assigned, used, remaining = {}, set(), []
    for item in items:
        name = item["name"]
        slug = json_slug(name)
        if slug in slug_map:
            assigned[name] = slug_map[slug]
            used.add(slug_map[slug])
        else:
            remaining.append(item)
    unused = [c for c in candidates if c not in used]
    for item in remaining:
        name = item["name"]
        tw = word_set(name)
        best, best_score = None, 0
        for c in unused:
            score = len(tw & word_set(c.stem))
            if score > best_score:
                best, best_score = c, score
        if best:
            assigned[name] = best
            unused.remove(best)
    return assigned


RESULT_MAP = assign_result_files()


def is_uncertain(v):
    if v is None:
        return True
    if isinstance(v, str) and (v.strip() == "" or "[uncertain]" in v):
        return True
    return False


def slugify(name):
    s = re.sub(r"[^a-z0-9\s-]", "", name.lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return re.sub(r"-+", "-", s)


VERDICT_META = {
    "no": ("Gap", "gap"),
    "partial": ("Sebagian", "partial"),
    "yes": ("Ada", "risk"),
}


def extract_verdict(value):
    if not isinstance(value, str):
        return None
    m = re.match(r"\s*(yes|no|partial)\b", value.strip(), re.IGNORECASE)
    if not m:
        return None
    return m.group(1).lower()


loaded = []
for item in items:
    name = item["name"]
    f = RESULT_MAP.get(name)
    data = json.loads(f.read_text()) if f else None
    uncertain_list = set((data or {}).get("uncertain", []) or [])
    verdict_raw = get_val = data.get("does_error_type_diagnosis") if data else None
    verdict = extract_verdict(verdict_raw) if not is_uncertain(verdict_raw) else None
    loaded.append({
        "item": item, "data": data, "uncertain": uncertain_list,
        "anchor": slugify(name), "verdict": verdict,
    })

# ---- stats ----
total = len(loaded)
cat_counts = {c: 0 for c in CATEGORY_ORDER}
verdict_counts = {"no": 0, "partial": 0, "yes": 0}
for e in loaded:
    if e["data"]:
        cat_counts[e["data"].get("category", "")] = cat_counts.get(e["data"].get("category", ""), 0) + 1
        if e["verdict"]:
            verdict_counts[e["verdict"]] += 1

FIELD_LABELS = {
    "origin_region": "Wilayah Asal", "target_age": "Usia Target", "delivery_mode": "Moda Layanan",
    "language_localization": "Lokalisasi Bahasa", "pricing_model": "Model Harga",
    "local_curriculum_alignment": "Keselarasan Kurikulum",
    "does_error_type_diagnosis": "Diagnosis Jenis Kesalahan", "diagnosis_granularity": "Granularitas Diagnosis",
    "diagnosis_input_modality": "Modalitas Input", "ai_tutor_diagnosis_reliability": "Reliabilitas Diagnosis AI",
    "how_parent_involved": "Peran Orang Tua", "ai_tutor_directly_to_child": "AI Bicara Langsung ke Anak",
    "study_scale_or_sample": "Skala Studi/Sampel", "evidence_strength": "Kekuatan Bukti",
    "remediation_efficacy_evidence": "Bukti Efikasi Remediasi",
}


def render_field(fname, value):
    label = FIELD_LABELS.get(fname, fname)
    if isinstance(value, list):
        items_html = "".join(f"<li>{escape(str(x))}</li>" for x in value)
        return f'<div class="field"><span class="field-label">{escape(label)}</span><ul class="field-list">{items_html}</ul></div>'
    return f'<div class="field"><span class="field-label">{escape(label)}</span><p class="field-value">{escape(str(value))}</p></div>'


def render_item(entry):
    item, data, anchor = entry["item"], entry["data"], entry["anchor"]
    name = item["name"]
    if not data:
        return f'<section class="card" id="{anchor}"><h3>{escape(name)}</h3><p class="muted">Belum ada hasil riset.</p></section>'

    uncertain = entry["uncertain"]
    cat = data.get("category", "")
    verdict = entry["verdict"]
    vlabel, vclass = VERDICT_META.get(verdict, ("Tidak diketahui", ""))

    meta_bits = []
    for f in ["origin_region", "target_age", "delivery_mode"]:
        v = data.get(f)
        if not is_uncertain(v) and f not in uncertain:
            meta_bits.append(f'<span>{escape(FIELD_LABELS.get(f, f))}: {escape(str(v)[:80])}</span>')

    key_finding = data.get("key_finding")
    key_finding_html = ""
    if key_finding and not is_uncertain(key_finding) and "key_finding" not in uncertain:
        key_finding_html = f'<p class="lead">{escape(key_finding)}</p>'

    evidence_quote = data.get("evidence_quote")
    quote_html = ""
    if evidence_quote and not is_uncertain(evidence_quote) and "evidence_quote" not in uncertain:
        quote_html = f'<blockquote>{escape(evidence_quote)}</blockquote>'

    consumed = {"name", "category", "key_finding", "evidence_quote", "source_urls", "uncertain",
                "origin_region", "target_age", "delivery_mode"}
    field_order = [
        "diagnosis_granularity", "diagnosis_input_modality", "ai_tutor_diagnosis_reliability",
        "how_parent_involved", "ai_tutor_directly_to_child",
        "language_localization", "pricing_model", "local_curriculum_alignment",
        "study_scale_or_sample", "evidence_strength", "remediation_efficacy_evidence",
    ]
    fields_html = []
    for f in field_order:
        v = data.get(f)
        if f in consumed or f in uncertain or is_uncertain(v):
            continue
        consumed.add(f)
        fields_html.append(render_field(f, v))

    sources = data.get("source_urls") or []
    sources_html = ""
    if sources and "source_urls" not in uncertain:
        links = "".join(
            f'<li><a href="{escape(u)}" target="_blank" rel="noopener">{escape(u)}</a></li>' for u in sources if isinstance(u, str)
        )
        sources_html = f'<details class="sources"><summary>Sumber ({len(sources)})</summary><ul class="source-list">{links}</ul></details>'

    return f'''<section class="card" id="{anchor}">
  <header class="card-head">
    <h3>{escape(name)}</h3>
    <div class="tags">
      <span class="tag">{escape(CATEGORY_LABELS.get(cat, cat))}</span>
      {f'<span class="pill pill-{vclass}">{escape(vlabel)}</span>' if verdict else ''}
    </div>
    {f'<div class="meta">{"".join(meta_bits)}</div>' if meta_bits else ''}
  </header>
  {key_finding_html}
  <div class="fields">{"".join(fields_html)}</div>
  {quote_html}
  {sources_html}
</section>'''


def render_toc_group(cat):
    entries = [e for e in loaded if e["data"] and e["data"].get("category") == cat]
    if not entries:
        return ""
    rows = []
    for e in entries:
        v = e["verdict"]
        vlabel, vclass = VERDICT_META.get(v, ("", ""))
        pill = f'<span class="pill pill-{vclass} pill-sm">{escape(vlabel)}</span>' if v else ""
        rows.append(f'<li><a href="#{e["anchor"]}">{escape(e["item"]["name"])}</a>{pill}</li>')
    return f'<div class="toc-group"><h4>{escape(CATEGORY_LABELS.get(cat, cat))} <span class="count">{len(entries)}</span></h4><ul>{"".join(rows)}</ul></div>'


cards_html = "\n".join(render_item(e) for e in loaded)
toc_html = "\n".join(render_toc_group(c) for c in CATEGORY_ORDER)

html = f"""<!doctype html>
<title>Peta Gap B/K/H</title>
<meta charset="utf-8">
<style>
:root {{
  --bg:#F4F6F8; --surface:#FFFFFF; --surface-2:#EAEDF1; --border:#D7DEE5;
  --ink:#161B22; --ink-soft:#54606F; --ink-faint:#8993A1;
  --accent:#1F6F6B; --accent-ink:#0E4643; --accent-soft:#DCEEEC;
  --sem-gap:#1F7A5C; --sem-gap-soft:#DFF3EA;
  --sem-risk:#A34A2B; --sem-risk-soft:#F3E3DC;
  --sem-partial:#8A6D1F; --sem-partial-soft:#F3ECD6;
  --font-display: ui-serif, Charter, 'Iowan Old Style', 'Palatino Linotype', Georgia, serif;
  --font-body: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  --font-mono: ui-monospace, 'SF Mono', 'Cascadia Code', Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg:#12161C; --surface:#181D25; --surface-2:#1F2530; --border:#2A313C;
    --ink:#E7EAEE; --ink-soft:#9AA5B1; --ink-faint:#5F6B79;
    --accent:#4FBDB6; --accent-ink:#8FE0D9; --accent-soft:#173330;
    --sem-gap:#4FBD8C; --sem-gap-soft:#16302A;
    --sem-risk:#D97A5C; --sem-risk-soft:#3A2019;
    --sem-partial:#D9B85C; --sem-partial-soft:#362C12;
  }}
}}
:root[data-theme="dark"] {{
  --bg:#12161C; --surface:#181D25; --surface-2:#1F2530; --border:#2A313C;
  --ink:#E7EAEE; --ink-soft:#9AA5B1; --ink-faint:#5F6B79;
  --accent:#4FBDB6; --accent-ink:#8FE0D9; --accent-soft:#173330;
  --sem-gap:#4FBD8C; --sem-gap-soft:#16302A;
  --sem-risk:#D97A5C; --sem-risk-soft:#3A2019;
  --sem-partial:#D9B85C; --sem-partial-soft:#362C12;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; background:var(--bg); color:var(--ink); font-family:var(--font-body);
  line-height:1.55; -webkit-font-smoothing:antialiased;
}}
a {{ color:var(--accent-ink); }}
::selection {{ background:var(--accent-soft); }}

header.top {{
  position:sticky; top:0; z-index:10; background:var(--surface); border-bottom:1px solid var(--border);
  padding:1.5rem 2rem;
}}
.top-inner {{ max-width:1180px; margin:0 auto; }}
.eyebrow {{
  font-family:var(--font-mono); font-size:0.72rem; letter-spacing:0.09em; text-transform:uppercase;
  color:var(--accent-ink); margin:0 0 0.4rem;
}}
h1 {{
  font-family:var(--font-display); font-size:clamp(1.6rem, 2.6vw, 2.3rem); margin:0 0 0.5rem;
  text-wrap:balance; font-weight:600; letter-spacing:-0.01em;
}}
.research-q {{ color:var(--ink-soft); max-width:74ch; margin:0 0 1.1rem; font-size:0.98rem; }}
.stats {{ display:flex; flex-wrap:wrap; gap:0.6rem; }}
.stat {{
  font-family:var(--font-mono); font-size:0.82rem; background:var(--surface-2); border:1px solid var(--border);
  border-radius:6px; padding:0.35rem 0.7rem; color:var(--ink-soft); font-variant-numeric:tabular-nums;
}}
.stat b {{ color:var(--ink); font-weight:600; }}

.layout {{ max-width:1180px; margin:0 auto; display:grid; grid-template-columns:260px 1fr; gap:2.2rem; padding:2rem; align-items:start; }}
@media (max-width:900px) {{ .layout {{ grid-template-columns:1fr; }} }}

nav.toc {{ position:sticky; top:6.5rem; max-height:calc(100vh - 8rem); overflow-y:auto; padding-right:0.5rem; }}
@media (max-width:900px) {{ nav.toc {{ position:static; max-height:none; }} }}
.toc-group h4 {{
  font-family:var(--font-mono); font-size:0.72rem; text-transform:uppercase; letter-spacing:0.07em;
  color:var(--ink-faint); margin:1.1rem 0 0.4rem; display:flex; justify-content:space-between;
}}
.toc-group:first-child h4 {{ margin-top:0; }}
.toc-group .count {{ color:var(--ink-faint); }}
.toc-group ul {{ list-style:none; margin:0; padding:0; }}
.toc-group li {{
  display:flex; align-items:center; justify-content:space-between; gap:0.5rem;
  padding:0.3rem 0; border-bottom:1px dashed var(--border);
}}
.toc-group a {{ text-decoration:none; color:var(--ink-soft); font-size:0.88rem; }}
.toc-group a:hover {{ color:var(--accent-ink); }}

main {{ min-width:0; }}
.summary-box {{
  background:var(--accent-soft); border:1px solid var(--accent); border-radius:10px;
  padding:1.3rem 1.5rem; margin-bottom:2rem;
}}
.summary-box h2 {{ font-family:var(--font-display); font-size:1.15rem; margin:0 0 0.6rem; }}
.summary-box p {{ margin:0 0 0.6rem; color:var(--ink); max-width:72ch; }}
.summary-box p:last-child {{ margin-bottom:0; }}

.card {{
  background:var(--surface); border:1px solid var(--border); border-radius:10px;
  padding:1.4rem 1.6rem; margin-bottom:1.1rem; scroll-margin-top:6rem;
}}
.card-head h3 {{ font-family:var(--font-display); font-size:1.25rem; margin:0 0 0.5rem; text-wrap:balance; }}
.tags {{ display:flex; gap:0.4rem; align-items:center; margin-bottom:0.5rem; flex-wrap:wrap; }}
.tag {{
  font-family:var(--font-mono); font-size:0.7rem; text-transform:uppercase; letter-spacing:0.05em;
  color:var(--ink-soft); background:var(--surface-2); border:1px solid var(--border);
  border-radius:100px; padding:0.15rem 0.6rem;
}}
.pill {{ font-family:var(--font-mono); font-size:0.72rem; border-radius:100px; padding:0.15rem 0.65rem; font-weight:600; }}
.pill-sm {{ font-size:0.66rem; padding:0.1rem 0.5rem; }}
.pill-gap {{ background:var(--sem-gap-soft); color:var(--sem-gap); }}
.pill-risk {{ background:var(--sem-risk-soft); color:var(--sem-risk); }}
.pill-partial {{ background:var(--sem-partial-soft); color:var(--sem-partial); }}
.meta {{ display:flex; gap:1rem; flex-wrap:wrap; font-size:0.82rem; color:var(--ink-faint); margin-bottom:0.8rem; }}
.lead {{ font-size:1.02rem; color:var(--ink); max-width:70ch; margin:0.6rem 0 1rem; }}

.fields {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(230px,1fr)); gap:0.9rem 1.4rem; margin:0.8rem 0; }}
.field-label {{
  display:block; font-family:var(--font-mono); font-size:0.68rem; text-transform:uppercase; letter-spacing:0.06em;
  color:var(--ink-faint); margin-bottom:0.2rem;
}}
.field-value {{ margin:0; font-size:0.9rem; color:var(--ink-soft); max-width:60ch; }}
.field-list {{ margin:0; padding-left:1.1rem; font-size:0.9rem; color:var(--ink-soft); }}

blockquote {{
  border-left:3px solid var(--accent); margin:1rem 0; padding:0.2rem 0 0.2rem 1rem;
  color:var(--ink-soft); font-style:italic; max-width:68ch;
}}
details.sources {{ margin-top:0.9rem; }}
details.sources summary {{
  cursor:pointer; font-family:var(--font-mono); font-size:0.78rem; color:var(--accent-ink);
}}
.source-list {{ margin:0.5rem 0 0; padding-left:1.2rem; font-size:0.78rem; word-break:break-all; }}
.source-list a {{ color:var(--ink-faint); }}
.muted {{ color:var(--ink-faint); }}

footer {{ max-width:1180px; margin:0 auto; padding:1rem 2rem 3rem; color:var(--ink-faint); font-size:0.8rem; }}

@media (prefers-reduced-motion:no-preference) {{
  .card {{ transition:border-color 0.15s; }}
  .card:hover {{ border-color:var(--accent); }}
}}
</style>

<header class="top">
  <div class="top-inner">
    <p class="eyebrow">Riset Pasar &middot; Diagnosis B/K/H</p>
    <h1>{escape(topic)}</h1>
    <p class="research-q">{escape(research_question)}</p>
    <div class="stats">
      <span class="stat"><b>{total}</b> item diriset</span>
      <span class="stat"><b>{verdict_counts['no']}</b> gap dikonfirmasi</span>
      <span class="stat"><b>{verdict_counts['partial']}</b> sebagian</span>
      <span class="stat"><b>{verdict_counts['yes']}</b> sudah ada di pasar</span>
    </div>
  </div>
</header>

<div class="layout">
  <nav class="toc">{toc_html}</nav>
  <main>
    <div class="summary-box">
      <h2>Ringkasan Eksekutif</h2>
      <p>Gap-nya nyata dan belum tertutup. Sembilan produk kompetitor (Ruangguru, Zenius, Quipper, CoLearn, QANDA, Kumon, Khan Academy Kids, IXL, Photomath) tidak mendiagnosis jenis kesalahan &mdash; semua berhenti di level skor atau topic-mastery. Eedi paling dekat tapi berbasis MCQ-distractor, bukan proses kerja anak.</p>
      <p><strong>Sparks Math</strong> &mdash; kompetitor offline Indonesia &mdash; sudah memakai bahasa B/K/H di materi marketing mereka tapi tidak punya instrumen untuk mengukurnya: sinyal permintaan pasar yang bersih, konsep tidak butuh edukasi pasar, hanya butuh instrumen.</p>
      <p>Riset stroke/handwriting analytics menunjukkan pendekatan input tulisan tangan valid secara akademik (AIED 2026, Kyoto LEAF/BookRoll) tapi belum pernah diterapkan untuk klasifikasi jenis-kesalahan pada anak SD &mdash; persis di titik kosong itulah OSN berada.</p>
    </div>
    {cards_html}
  </main>
</div>

<footer>Disusun dari 18 item riset (produk kompetitor, benchmark diagnostik, kerangka akademik, sinyal pasar) &middot; sumber lengkap tersedia di tiap kartu.</footer>
"""

(BASE / "report.html").write_text(html)
print(f"Wrote report.html ({len(html)} chars)")
