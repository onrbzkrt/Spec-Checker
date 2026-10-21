"""Generate fictional interior-part spec PDFs + a design standard for the Spec Checker demo."""
import csv
import os
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

OUT = sys.argv[1]
SPECS = os.path.join(OUT, "specs")
STD = os.path.join(OUT, "standards")
os.makedirs(SPECS, exist_ok=True)
os.makedirs(STD, exist_ok=True)

COMPANY = "Corvane Motors"
DIV = "Interior Development Division"
FOOTER = "Fictional sample data for a portfolio demo. Corvane Motors and all suppliers are invented."

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=16, spaceAfter=4, textColor=colors.HexColor("#1F2A44"))
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12, spaceBefore=10, spaceAfter=4, textColor=colors.HexColor("#1F2A44"))
BODY = ParagraphStyle("B", parent=ss["Normal"], fontSize=10, leading=14)
SMALL = ParagraphStyle("S", parent=ss["Normal"], fontSize=8, leading=10, textColor=colors.grey)

GRID = TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B8C0CC")),
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8ECF2")),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 9.5),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
])
KV = TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B8C0CC")),
    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8ECF2")),
    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 9.5),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
])


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.grey)
    canvas.drawString(0.75 * inch, 0.5 * inch, FOOTER)
    canvas.drawRightString(7.75 * inch, 0.5 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build(path, story, title):
    doc = SimpleDocTemplate(path, pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.7 * inch, bottomMargin=0.8 * inch, title=title, author=COMPANY)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


# ---------------------------------------------------------------- standard
APPROVED = {
    "Instrument Panel": ["PP-TD20", "PC/ABS"],
    "Door Trim": ["PP-TD20", "PP-GF20"],
    "Console": ["ABS", "PC/ABS"],
    "Seat Foam": ["PU Foam"],
    "Headliner": ["PET Fiber Composite"],
    "Pillar Trim": ["PP-TD20", "TPO"],
}


def standard():
    s = [Paragraph(f"{COMPANY} | {DIV}", SMALL),
         Paragraph("CM-IDS-001 Interior Component Design Standard", H1),
         Paragraph("Revision C | Effective 2026-03-01 | Owner: Interior Engineering Standards Group", BODY),
         Spacer(1, 8)]

    s += [Paragraph("1. Scope", H2),
          Paragraph("This standard defines the minimum requirements every interior component specification must meet "
                    "before release. It applies to instrument panel, door trim, console, seat foam, headliner and "
                    "pillar trim components. Each released specification is checked against Sections 2 to 8. "
                    "The overall validation result is the most severe result of any single check (Section 9).", BODY)]

    s += [Paragraph("2. Approved Materials", H2),
          Paragraph("Only the materials below may be used for each component category. Any other material "
                    "requires a deviation approved by the Engineering Review Board and is otherwise a FAIL.", BODY),
          Spacer(1, 4)]
    rows = [["Component category", "Approved materials"]] + [[k, ", ".join(v)] for k, v in APPROVED.items()]
    t = Table(rows, colWidths=[2.3 * inch, 4.4 * inch]); t.setStyle(GRID); s.append(t)

    s += [Paragraph("3. Mass Targets", H2),
          Paragraph("Actual mass is compared with the target mass recorded on the specification.", BODY), Spacer(1, 4)]
    t = Table([["Actual / target", "Result"], ["Up to 105%", "PASS"], ["Above 105% up to 110%", "WARNING"],
               ["Above 110%", "FAIL"]], colWidths=[3.35 * inch, 3.35 * inch]); t.setStyle(GRID); s.append(t)

    s += [Paragraph("4. Cost Targets", H2),
          Paragraph("Actual piece cost (USD) is compared with the target piece cost.", BODY), Spacer(1, 4)]
    t = Table([["Actual / target", "Result"], ["Up to 103%", "PASS"], ["Above 103% up to 108%", "WARNING"],
               ["Above 108%", "FAIL"]], colWidths=[3.35 * inch, 3.35 * inch]); t.setStyle(GRID); s.append(t)

    s += [Paragraph("5. Flammability", H2),
          Paragraph("All interior materials must meet FMVSS 302 (burn rate not more than 102 mm/min). "
                    "The internal design target is 80 mm/min or less to keep margin for supplier variation.", BODY),
          Spacer(1, 4)]
    t = Table([["Burn rate (mm/min)", "Result"], ["80 or less", "PASS"], ["Above 80 up to 102", "WARNING"],
               ["Above 102", "FAIL (does not meet FMVSS 302)"]], colWidths=[3.35 * inch, 3.35 * inch])
    t.setStyle(GRID); s.append(t)

    s += [Paragraph("6. Odor", H2),
          Paragraph("Odor is rated with VDA 270 on a 1 to 6 scale (lower is better).", BODY), Spacer(1, 4)]
    t = Table([["VDA 270 rating", "Result"], ["3.0 or less", "PASS"], ["3.5", "WARNING"], ["4.0 or higher", "FAIL"]],
              colWidths=[3.35 * inch, 3.35 * inch]); t.setStyle(GRID); s.append(t)

    s += [Paragraph("7. Seat Foam Density", H2),
          Paragraph("Seat foam density must be between 45 and 60 kg/m3 (inclusive). Outside this range is a FAIL "
                    "because of durability and comfort risk.", BODY)]

    s += [Paragraph("8. Documentation", H2),
          Paragraph("Every specification must include: part number, revision letter, component category, material, "
                    "target and actual mass, target and actual cost, flammability result, odor rating, supplier and "
                    "engineer approval. A specification marked DRAFT, or without engineer approval, is a WARNING and "
                    "cannot be released until corrected.", BODY)]

    s += [Paragraph("9. Validation Outcome and Escalation", H2),
          Paragraph("The overall result is the most severe individual result (FAIL over WARNING over PASS).", BODY),
          Spacer(1, 4)]
    t = Table([["Overall result", "Required action"],
               ["PASS", "Specification may be released."],
               ["WARNING", "Responsible engineer adds a written justification within 3 business days."],
               ["FAIL", "Escalate to the Engineering Review Board within 5 business days."]],
              colWidths=[1.6 * inch, 5.1 * inch]); t.setStyle(GRID); s.append(t)

    s += [Paragraph("10. Contacts", H2),
          Paragraph("Standard owner: Interior Engineering Standards Group. Engineering Review Board meets every "
                    "Tuesday. Deviation requests are submitted through the Interior Engineering SharePoint site.", BODY)]

    s += [Paragraph("Revision History", H2)]
    t = Table([["Rev", "Date", "Change"], ["A", "2024-09-15", "Initial release"],
               ["B", "2025-05-02", "Added VDA 270 odor requirement"],
               ["C", "2026-03-01", "Tightened cost FAIL threshold from 110% to 108%"]],
              colWidths=[0.6 * inch, 1.2 * inch, 4.9 * inch]); t.setStyle(GRID); s.append(t)

    build(os.path.join(STD, "CM-IDS-001_Interior_Component_Design_Standard_RevC.pdf"), s,
          "CM-IDS-001 Interior Component Design Standard Rev C")


# ---------------------------------------------------------------- specs
PARTS = [
    dict(pn="INT-IP-1001", name="Instrument Panel Upper Substrate", cat="Instrument Panel", mat="PP-TD20",
         wt=2850, wa=2910, ct=18.40, ca=18.75, burn=62, odor=2.5, sup="Brightline Polymers", eng="J. Patel",
         rev="B", tmpl="A"),
    dict(pn="INT-DR-2003", name="Front Door Trim Panel LH", cat="Door Trim", mat="PP-TD20",
         wt=1650, wa=1790, ct=12.10, ca=12.30, burn=70, odor=3.0, sup="Halvard Trim Systems", eng="M. Alvarez",
         rev="C", tmpl="B"),
    dict(pn="INT-CN-3002", name="Center Console Storage Bin", cat="Console", mat="ABS",
         wt=980, wa=975, ct=7.80, ca=8.70, burn=55, odor=2.5, sup="Brightline Polymers", eng="K. Nguyen",
         rev="A", tmpl="C"),
    dict(pn="INT-ST-4001", name="Driver Seat Cushion Foam", cat="Seat Foam", mat="PU Foam", dens=52,
         wt=1450, wa=1460, ct=21.00, ca=21.40, burn=95, odor=3.5, sup="Meridale Foam Co.", eng="R. Chen",
         rev="B", tmpl="A"),
    dict(pn="INT-HL-5001", name="Headliner Substrate", cat="Headliner", mat="PET Fiber Composite",
         wt=2100, wa=2080, ct=15.50, ca=15.20, burn=48, odor=2.0, sup="Ostrova Composites", eng="J. Patel",
         rev="D", tmpl="B"),
    dict(pn="INT-PL-6002", name="A-Pillar Trim RH", cat="Pillar Trim", mat="ABS",
         wt=420, wa=430, ct=3.10, ca=3.12, burn=60, odor=2.5, sup="Halvard Trim Systems", eng="M. Alvarez",
         rev="A", tmpl="C"),
    dict(pn="INT-DR-2004", name="Rear Door Trim Panel RH", cat="Door Trim", mat="PP-GF20",
         wt=1480, wa=1520, ct=10.90, ca=11.10, burn=110, odor=3.0, sup="Halvard Trim Systems", eng="K. Nguyen",
         rev="B", tmpl="A"),
    dict(pn="INT-CN-3005", name="Console Armrest Lid", cat="Console", mat="PC/ABS",
         wt=640, wa=655, ct=5.60, ca=5.75, burn=58, odor=2.5, sup="Brightline Polymers", eng=None,
         rev="DRAFT", tmpl="B"),
    dict(pn="INT-IP-1004", name="Glovebox Door", cat="Instrument Panel", mat="PC/ABS",
         wt=760, wa=800, ct=6.20, ca=6.45, burn=64, odor=3.0, sup="Brightline Polymers", eng="R. Chen",
         rev="C", tmpl="C"),
    dict(pn="INT-ST-4003", name="Rear Seat Back Foam", cat="Seat Foam", mat="PU Foam", dens=41,
         wt=1210, wa=1190, ct=14.80, ca=14.60, burn=75, odor=2.5, sup="Meridale Foam Co.", eng="J. Patel",
         rev="A", tmpl="A"),
]

SEV = {"PASS": 0, "WARNING": 1, "FAIL": 2}


def band(v, p, w):
    return "PASS" if v <= p else ("WARNING" if v <= w else "FAIL")


def evaluate(p):
    r = {}
    r["material"] = "PASS" if p["mat"] in APPROVED[p["cat"]] else "FAIL"
    r["mass"] = band(p["wa"] / p["wt"], 1.05, 1.10)
    r["cost"] = band(p["ca"] / p["ct"], 1.03, 1.08)
    r["flammability"] = band(p["burn"], 80, 102)
    r["odor"] = "PASS" if p["odor"] <= 3.0 else ("WARNING" if p["odor"] < 4.0 else "FAIL")
    if p["cat"] == "Seat Foam":
        r["density"] = "PASS" if 45 <= p["dens"] <= 60 else "FAIL"
    r["documentation"] = "PASS" if (p["rev"] != "DRAFT" and p["eng"]) else "WARNING"
    overall = max(r.values(), key=lambda x: SEV[x])
    reasons = [k for k, v in r.items() if v != "PASS"]
    return overall, reasons


def header(p):
    return [Paragraph(f"{COMPANY} | {DIV}", SMALL),
            Paragraph(f"Component Specification: {p['name']}", H1),
            Paragraph(f"Part number <b>{p['pn']}</b> | Revision <b>{p['rev']}</b> | Category: {p['cat']}", BODY),
            Spacer(1, 8)]


def approval(p):
    if p["eng"]:
        return Paragraph(f"<b>Engineer approval:</b> {p['eng']}, Interior Engineering, 2026-10-{(sum(map(ord, p['pn'])) % 9) + 10}", BODY)
    return Paragraph("<b>Engineer approval:</b> Pending. Document status: DRAFT, not for release.", BODY)


def tmpl_a(p):  # table-heavy
    s = header(p)
    s.append(Paragraph("Design Data", H2))
    rows = [["Property", "Target", "Actual", "Unit"],
            ["Mass", f"{p['wt']:,}", f"{p['wa']:,}", "g"],
            ["Piece cost", f"{p['ct']:.2f}", f"{p['ca']:.2f}", "USD"]]
    t = Table(rows, colWidths=[2.2 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch]); t.setStyle(GRID); s.append(t)
    s.append(Paragraph("Material and Supplier", H2))
    kv = [["Material", p["mat"]], ["Supplier", p["sup"]]]
    if "dens" in p:
        kv.append(["Foam density", f"{p['dens']} kg/m3"])
    t = Table(kv, colWidths=[2.2 * inch, 4.5 * inch]); t.setStyle(KV); s.append(t)
    s.append(Paragraph("Test Results", H2))
    t = Table([["Test", "Method", "Result"],
               ["Flammability", "FMVSS 302", f"{p['burn']} mm/min"],
               ["Odor", "VDA 270", f"{p['odor']}"]], colWidths=[2.2 * inch, 2.2 * inch, 2.3 * inch])
    t.setStyle(GRID); s.append(t)
    s += [Spacer(1, 12), approval(p)]
    return s


def tmpl_b(p):  # narrative
    s = header(p)
    kg_t, kg_a = p["wt"] / 1000, p["wa"] / 1000
    s.append(Paragraph("Summary", H2))
    s.append(Paragraph(
        f"The {p['name'].lower()} is molded from {p['mat']} and supplied by {p['sup']}. The program target mass "
        f"is {kg_t:.3f} kg; the latest production-intent sample weighed {kg_a:.3f} kg. Target piece cost was set "
        f"at ${p['ct']:.2f}, and the current supplier quotation is ${p['ca']:.2f} per piece.", BODY))
    s.append(Paragraph("Validation Testing", H2))
    s.append(Paragraph(
        f"Flammability testing per FMVSS 302 measured a burn rate of {p['burn']} mm/min. Odor evaluation per "
        f"VDA 270 resulted in a rating of {p['odor']}. No other open test items are recorded for this revision.", BODY))
    s.append(Paragraph("Notes", H2))
    s.append(Paragraph("Tooling is at the supplier. Color and grain match approved against the master sample.", BODY))
    s += [Spacer(1, 12), approval(p)]
    return s


def tmpl_c(p):  # key-value form
    s = header(p)
    s.append(Paragraph("Specification Sheet", H2))
    kv = [["Part number", p["pn"]], ["Revision", p["rev"]], ["Component category", p["cat"]],
          ["Material", p["mat"]], ["Supplier", p["sup"]],
          ["Mass target / actual", f"{p['wt']} g / {p['wa']} g"],
          ["Cost target / actual", f"${p['ct']:.2f} / ${p['ca']:.2f}"],
          ["FMVSS 302 burn rate", f"{p['burn']} mm/min"],
          ["VDA 270 odor", f"{p['odor']}"]]
    t = Table(kv, colWidths=[2.4 * inch, 4.3 * inch]); t.setStyle(KV); s.append(t)
    s.append(Paragraph("Engineering Comments", H2))
    s.append(Paragraph("Specification prepared for gateway review. Supplier PPAP documents are stored separately.", BODY))
    s += [Spacer(1, 12), approval(p)]
    return s


TEMPLATES = {"A": tmpl_a, "B": tmpl_b, "C": tmpl_c}

standard()
key_rows = []
for p in PARTS:
    fname = f"{p['pn']}_{p['name'].replace(' ', '_').replace('/', '-')}.pdf"
    build(os.path.join(SPECS, fname), TEMPLATES[p["tmpl"]](p), f"{p['pn']} {p['name']}")
    overall, reasons = evaluate(p)
    key_rows.append([p["pn"], p["name"], p["cat"], p["mat"], overall, "; ".join(reasons) or "-", fname])

with open(os.path.join(OUT, "answer_key.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["part_number", "part_name", "category", "material", "expected_result", "failed_checks", "file"])
    w.writerows(key_rows)

for r in key_rows:
    print(r[0], r[4], r[5])
