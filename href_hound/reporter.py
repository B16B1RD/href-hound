import datetime
import html


def generate_report(results: list, output_path: str):
    """
    リンクチェック結果（LinkResultのlist）をHTMLファイルとして出力。
    """
    broken = [r for r in results if getattr(r, "is_broken", False)]
    grouped: dict[str, list] = {}
    for r in broken:
        grouped.setdefault(r.source, []).append(r)

    doc = []
    doc.append("<!DOCTYPE html><html><head>")
    doc.append("<meta charset='utf-8'><title>Link Checker Report</title>")
    doc.append("""<style>
body { font-family: Arial, sans-serif; }
h2 { margin-top: 1.5em; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
th { background-color: #eee; }
tr:nth-child(even) { background-color: #f9f9f9; }
.error { color: red; }
</style>""")
    doc.append("</head><body>")
    doc.append("<h1>Link Checker Report</h1>")
    doc.append(f"<p>Generated: {datetime.datetime.now().isoformat()}</p>")

    if broken:
        for source, items in grouped.items():
            # Source page URL as clickable link
            esc_src = html.escape(source, quote=True)
            doc.append(f'<h2>Page: <a href="{esc_src}">{esc_src}</a></h2>')
            doc.append("<table>")
            doc.append("<tr><th>Broken Link</th><th>Status</th><th>Error</th></tr>")
            for r in items:
                tgt = html.escape(r.target)
                status = r.status if r.status is not None else ""
                err = html.escape(r.error) if r.error else ""
                doc.append(
                    f"<tr><td><a href=\"{tgt}\">{tgt}</a></td>"
                    f"<td class=\"error\">{status}</td>"
                    f"<td class=\"error\">{err}</td></tr>"
                )
            doc.append("</table>")
    else:
        doc.append("<p>No broken links found.</p>")

    doc.append("</body></html>")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(doc))