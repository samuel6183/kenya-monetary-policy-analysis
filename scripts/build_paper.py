"""Render the repository working paper with integrated chart SVGs."""
from pathlib import Path
import markdown
from weasyprint import HTML
root=Path(__file__).resolve().parents[1]
body=markdown.markdown((root/"RESEARCH_PAPER.md").read_text(),extensions=["tables","fenced_code","toc"])
css="""
@page { size: A4; margin: 19mm 19mm 20mm; @bottom-left { content: "KENYA MONETARY POLICY | WORKING PAPER"; font-size: 8pt; color: #62717c; } @bottom-right { content: counter(page) " / " counter(pages); font-size: 9pt; color: #62717c; } }
body { font-family: 'DejaVu Sans', sans-serif; color:#243541; font-size:10pt; line-height:1.55; }
h1 { font-size:27pt; color:#15394d; margin:0 0 8mm; line-height:1.13; }
h2 { font-size:17pt; color:#15394d; margin-top:9mm; break-after:avoid; }
h3 { font-size:12pt; color:#17698a; break-after:avoid; }
p { orphans:3; widows:3; } a { color:#155d7b; overflow-wrap:anywhere; }
img { display:block; max-width:100%; max-height:175mm; margin:4mm auto; }
p:has(img) { break-inside:avoid; break-after:avoid; }
table { border-collapse:collapse; width:100%; font-size:8.7pt; margin:4mm 0; }
th { background:#173e51; color:white; text-align:left; } td,th { padding:2mm; border-bottom:0.5pt solid #d7e1e7; }
tr { break-inside:avoid; } tr:nth-child(even) td { background:#f2f6f7; }
pre { background:#f2f6f7; padding:4mm; white-space:pre-wrap; overflow-wrap:anywhere; font-size:8.5pt; }
li { margin:1mm 0; } 
"""
HTML(string=f'<!doctype html><html lang="en"><head><meta charset="utf-8"><style>{css}</style></head><body>{body}</body></html>',base_url=str(root)+"/").write_pdf(root/"RESEARCH_PAPER.pdf")
