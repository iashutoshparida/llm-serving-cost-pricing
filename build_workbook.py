"""Builds model/serving_cost_pricing.xlsx with live formulas.

Blue = input, black = formula, green = link to another sheet,
yellow fill = assumption to replace with measured data.
"""
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

F = "Arial"
BLUE = Font(name=F, color="0000FF")
BLACK = Font(name=F)
GREEN = Font(name=F, color="008000")
BOLD = Font(name=F, bold=True)
TITLE = Font(name=F, bold=True, size=13)
YELLOW = PatternFill("solid", fgColor="FFFF00")
HEAD = PatternFill("solid", fgColor="D9E1F2")

wb = Workbook()

# ---------------------------------------------------------------- Inputs
ws = wb.active
ws.title = "Inputs"
ws["A1"] = "ReviewPulse serving cost & pricing model: inputs"; ws["A1"].font = TITLE
ws["A2"] = "Edit blue cells only. Yellow = assumption to replace with measured data (see README)."
ws["A2"].font = Font(name=F, italic=True)
for c, h in zip("ABCD", ["Input", "Value", "Unit", "Source / note"]):
    ws[f"{c}4"] = h; ws[f"{c}4"].font = BOLD; ws[f"{c}4"].fill = HEAD

rows = [
    # key, label, value, unit, source, assumption?, fmt
    ("chars", "Average review length", 710, "characters", "Measured: 10,000 Yelp reviews, ReviewPulse results/eval_results.json", False, "#,##0"),
    ("sents", "Average sentences per review", 9.5, "sentences", "Measured: same run", False, "0.0"),
    ("cpt", "Characters per token", 4, "chars/token", "A1: English average; replace with Gemini usage_metadata", True, "0.0"),
    ("tagprompt", "Tagging prompt tokens per 25-sentence batch", 120, "tokens", "From ReviewPulse prompt (taggers.py)", False, "#,##0"),
    ("tagout", "Tagging output tokens per sentence", 12, "tokens", "From ReviewPulse JSON output format", False, "#,##0"),
    ("repprompt", "Reply prompt tokens", 110, "tokens", "From ReviewPulse prompt (replies.py)", False, "#,##0"),
    ("repout", "Reply output tokens", 110, "tokens", "About 80 words", False, "#,##0"),
    ("flin", "Gemini 3.1 Flash-Lite input price", 0.25, "$ per 1M tokens", "ai.google.dev/gemini-api/docs/pricing, paid tier, checked 23 Nov 2026", False, "$0.00"),
    ("flout", "Gemini 3.1 Flash-Lite output price", 1.50, "$ per 1M tokens", "Same source", False, "$0.00"),
    ("fin", "Gemini 3.6 Flash input price (from 1 Jan 2027)", 1.50, "$ per 1M tokens", "cloud.google.com/vertex-ai/generative-ai/pricing, standard price from Jan 2027", False, "$0.00"),
    ("fout", "Gemini 3.6 Flash output price (from 1 Jan 2027)", 7.50, "$ per 1M tokens", "Same source", False, "$0.00"),
    ("l4od", "L4 GPU VM, on-demand (g2-standard-8)", 0.853624312, "$ per hour", "cloud.google.com/products/compute/pricing/accelerator-optimized, checked 23 Nov 2026", False, "$0.000"),
    ("l4spot", "L4 GPU VM, spot (g2-standard-8)", 0.340572, "$ per hour", "Same source; spot can be pre-empted", False, "$0.000"),
    ("tps", "Aggregate decode throughput on one L4", 800, "output tokens/s", "A2: placeholder until bench/vllm_benchmark.ipynb results replace it", True, "#,##0"),
    ("util", "GPU utilisation", 0.40, "share of hours busy", "A3: planning assumption", True, "0%"),
    ("prefill", "Prompt-processing overhead", 1.25, "multiplier on decode time", "A4: planning assumption; bench measures it", True, "0.00"),
    ("opsh", "Engineer time to run self-hosting", 8, "hours per month", "A5: planning assumption", True, "#,##0"),
    ("opsr", "Loaded cost of that time", 12, "$ per hour", "A6: planning assumption", True, "$0"),
    ("hours", "Hours per month", 730, "hours", "Standard cloud billing month", False, "#,##0"),
    ("fx", "USD to INR", 84, "INR per $", "A7: planning rate", True, "#,##0.0"),
    ("wa", "WhatsApp utility message (India)", 0.115, "INR per message, before GST", "Meta WhatsApp Business Platform India rate card from 1 Oct 2026", False, "0.000"),
    ("gst", "GST", 0.18, "rate", "India GST on services", False, "0%"),
    ("pg", "Payment gateway fee", 0.02, "share of price, before GST", "Razorpay standard domestic pricing (2% + 18% GST)", False, "0.0%"),
]
ref = {}
for i, (key, label, val, unit, src, assume, fmt) in enumerate(rows, start=5):
    ws[f"A{i}"] = label; ws[f"A{i}"].font = BLACK
    ws[f"B{i}"] = val; ws[f"B{i}"].font = BLUE; ws[f"B{i}"].number_format = fmt
    if assume:
        ws[f"B{i}"].fill = YELLOW
    ws[f"C{i}"] = unit; ws[f"D{i}"] = src
    for c in "CD":
        ws[f"{c}{i}"].font = BLACK
    ref[key] = f"Inputs!$B${i}"
r = 5 + len(rows) + 1
ws[f"A{r}"] = "Derived workload"; ws[f"A{r}"].font = BOLD
derived = [
    ("tin", "Input tokens per review (tag + reply)", f"=B5/B7+B8*B6/25+B10+B5/B7", "#,##0"),
    ("tout", "Output tokens per review (tag + reply)", f"=B9*B6+B11", "#,##0"),
]
for j, (key, label, formula, fmt) in enumerate(derived, start=r + 1):
    ws[f"A{j}"] = label; ws[f"B{j}"] = formula; ws[f"B{j}"].number_format = fmt
    ws[f"A{j}"].font = BLACK; ws[f"B{j}"].font = BLACK
    ws[f"C{j}"] = "tokens"; ws[f"D{j}"] = "Formula from the inputs above"
    ref[key] = f"Inputs!$B${j}"
ws.column_dimensions["A"].width = 46
ws.column_dimensions["B"].width = 14
ws.column_dimensions["C"].width = 26
ws.column_dimensions["D"].width = 78

R = ref  # short alias

# ------------------------------------------------------- API vs self-host
s = wb.create_sheet("API vs Self-host")
s["A1"] = "Cost per 1,000 reviews and monthly break-even"; s["A1"].font = TITLE
s["A3"] = "Hosted API"; s["A3"].font = BOLD
for c, h in zip("ABC", ["Model", "$ per 1,000 reviews", "INR per restaurant-month (100 reviews)"]):
    s[f"{c}4"] = h; s[f"{c}4"].font = BOLD; s[f"{c}4"].fill = HEAD
s["A5"] = "Gemini 3.1 Flash-Lite"
s["B5"] = f"=({R['tin']}*{R['flin']}+{R['tout']}*{R['flout']})/1000000*1000"
s["A6"] = "Gemini 3.6 Flash (from Jan 2027)"
s["B6"] = f"=({R['tin']}*{R['fin']}+{R['tout']}*{R['fout']})/1000000*1000"
for rr in (5, 6):
    s[f"B{rr}"].number_format = "$0.000"; s[f"B{rr}"].font = GREEN
    s[f"C{rr}"] = f"=B{rr}/1000*100*{R['fx']}"; s[f"C{rr}"].number_format = "#,##0.00"; s[f"C{rr}"].font = BLACK

s["A8"] = "Self-hosted open 7-8B model on one L4"; s["A8"].font = BOLD
hdr = ["GPU pricing", "$ per hour", "Throughput (out tok/s)", "Reviews per busy hour", "Marginal $ per 1,000 reviews",
       "Fixed $ per month (GPU + ops)", "Capacity (reviews/month at utilisation)", "Break-even vs Flash-Lite (reviews/month)",
       "Break-even vs Flash (reviews/month)", "Capacity covers Flash-Lite break-even?"]
for k, h in enumerate(hdr):
    cell = s.cell(row=9, column=k + 1, value=h); cell.font = BOLD; cell.fill = HEAD
    cell.alignment = Alignment(wrap_text=True, vertical="top")
s.row_dimensions[9].height = 45
row = 10
for label, key in (("On-demand", "l4od"), ("Spot", "l4spot")):
    for mult in (0.375, 1.0, 1.875):  # 300 / 800 / 1500 tok/s around the input value
        s[f"A{row}"] = label
        s[f"B{row}"] = f"={R[key]}"; s[f"B{row}"].font = GREEN; s[f"B{row}"].number_format = "$0.000"
        s[f"C{row}"] = f"={R['tps']}*{mult}"; s[f"C{row}"].number_format = "#,##0"
        s[f"D{row}"] = f"=C{row}*3600/({R['tout']}*{R['prefill']})"; s[f"D{row}"].number_format = "#,##0"
        s[f"E{row}"] = f"=B{row}/D{row}*1000"; s[f"E{row}"].number_format = "$0.000"
        s[f"F{row}"] = f"=B{row}*{R['hours']}+{R['opsh']}*{R['opsr']}"; s[f"F{row}"].number_format = "$#,##0"
        s[f"G{row}"] = f"=D{row}*{R['util']}*{R['hours']}"; s[f"G{row}"].number_format = "#,##0"
        s[f"H{row}"] = f"=F{row}/($B$5/1000)"; s[f"H{row}"].number_format = "#,##0"
        s[f"I{row}"] = f"=F{row}/($B$6/1000)"; s[f"I{row}"].number_format = "#,##0"
        s[f"J{row}"] = f'=IF(G{row}>=H{row},"Yes","No: API stays cheaper")'
        for c in "CDEFGHIJ":
            s[f"{c}{row}"].font = BLACK
        row += 1
s[f"A{row+1}"] = "Read: break-even = fixed monthly self-hosting cost / API cost per review. Below it, the API is cheaper. Throughput rows are 0.375x, 1x and 1.875x the Inputs value."
s[f"A{row+1}"].font = Font(name=F, italic=True)
s[f"A{row+2}"] = "Restaurants needed at break-even (100 reviews each, on-demand, middle row):"
s[f"H{row+2}"] = "=H11/100"; s[f"H{row+2}"].number_format = "#,##0"; s[f"H{row+2}"].font = BLACK
s.column_dimensions["A"].width = 34
for k in range(2, 11):
    s.column_dimensions[get_column_letter(k)].width = 17

# ---------------------------------------------------------------- Pricing
p = wb.create_sheet("Pricing")
p["A1"] = "Pricing tiers: unit economics per customer per month (INR)"; p["A1"].font = TITLE
p["A2"] = "Prices are hypotheses (H1) to test with the willingness-to-pay survey in docs/pricing_research.md."
p["A2"].font = Font(name=F, italic=True)
ph = ["Tier", "Price (INR/month)", "Reviews processed", "WhatsApp digests", "Hosting share (INR)",
      "API cost (INR)", "WhatsApp cost incl. GST (INR)", "Gateway fee incl. GST (INR)", "COGS (INR)", "Gross margin (INR)", "Gross margin %"]
for k, h in enumerate(ph):
    cell = p.cell(row=4, column=k + 1, value=h); cell.font = BOLD; cell.fill = HEAD
    cell.alignment = Alignment(wrap_text=True, vertical="top")
p.row_dimensions[4].height = 45
tiers = [("Free", 0, 30, 0, 10), ("Starter", 299, 100, 4, 25), ("Pro", 799, 300, 30, 25)]
for i, (name, price, revs, wa, host) in enumerate(tiers, start=5):
    p[f"A{i}"] = name
    for c, v in zip("BCDE", (price, revs, wa, host)):
        p[f"{c}{i}"] = v; p[f"{c}{i}"].font = BLUE
    p[f"B{i}"].fill = YELLOW; p[f"E{i}"].fill = YELLOW
    p[f"F{i}"] = f"='API vs Self-host'!$B$5/1000*C{i}*{R['fx']}"
    p[f"G{i}"] = f"=D{i}*{R['wa']}*(1+{R['gst']})"
    p[f"H{i}"] = f"=B{i}*{R['pg']}*(1+{R['gst']})"
    p[f"I{i}"] = f"=E{i}+F{i}+G{i}+H{i}"
    p[f"J{i}"] = f"=B{i}-I{i}"
    p[f"K{i}"] = f'=IF(B{i}>0,J{i}/B{i},"-")'
    for c in "FGHIJ":
        p[f"{c}{i}"].number_format = "#,##0.00;(#,##0.00);-"; p[f"{c}{i}"].font = BLACK
    p[f"K{i}"].number_format = "0.0%"; p[f"K{i}"].font = BLACK
    for c in "BCDE":
        p[f"{c}{i}"].number_format = "#,##0"
p["B5"].comment = Comment("Free tier: template replies only, used to start the funnel.", "model")
p["A9"] = "Payback on customer acquisition"; p["A9"].font = BOLD
p["A10"] = "Cost to acquire one paying customer (INR)"; p["B10"] = 1500; p["B10"].font = BLUE; p["B10"].fill = YELLOW
p["C10"] = "A10: field sales near campus; replace with pilot data"
p["A11"] = "Monthly churn"; p["B11"] = 0.06; p["B11"].font = BLUE; p["B11"].fill = YELLOW; p["B11"].number_format = "0.0%"
p["C11"] = "A11: planning assumption"
for c, h in zip("ABCD", ["Tier", "Payback (months)", "Expected lifetime (months)", "Lifetime gross margin / CAC"]):
    p[f"{c}13"] = h; p[f"{c}13"].font = BOLD; p[f"{c}13"].fill = HEAD
for i, src in zip((14, 15), (6, 7)):
    p[f"A{i}"] = f"=A{src}"
    p[f"B{i}"] = f"=$B$10/J{src}"; p[f"B{i}"].number_format = "0.0"
    p[f"C{i}"] = "=1/$B$11"; p[f"C{i}"].number_format = "0.0"
    p[f"D{i}"] = f"=J{src}*C{i}/$B$10"; p[f"D{i}"].number_format = "0.0x"
    for c in "ABCD":
        p[f"{c}{i}"].font = BLACK
p.column_dimensions["A"].width = 40
for k in range(2, 12):
    p.column_dimensions[get_column_letter(k)].width = 15

# ------------------------------------------------------------ Sensitivity
t = wb.create_sheet("Sensitivity")
t["A1"] = "Break-even volume (reviews/month): on-demand L4 vs the API, by API price and engineer time"; t["A1"].font = TITLE
t["A3"] = "API price as a multiple of Flash-Lite list \u2193 / ops hours per month \u2192"; t["A3"].font = BOLD
ops = [0, 8, 20, 40]
mults = [0.5, 1, 2, 5.275]
labels = ["0.5x (batch / discount)", "1x Flash-Lite list", "2x", "5.3x (= Gemini 3.6 Flash from Jan 2027)"]
for k, o in enumerate(ops, start=2):
    c = t.cell(row=3, column=k, value=o); c.font = BLUE; c.fill = HEAD
t.cell(row=3, column=7, value="Restaurants at break-even (100 reviews each, 8 ops hours)").font = BOLD
for i, (m, lab) in enumerate(zip(mults, labels), start=4):
    c = t.cell(row=i, column=1, value=m); c.font = BLUE; c.number_format = "0.0##x"
    t.cell(row=i, column=6, value=lab).font = BLACK
    for k in range(2, 2 + len(ops)):
        col = get_column_letter(k)
        cell = t.cell(row=i, column=k,
                      value=f"=({R['l4od']}*{R['hours']}+{col}$3*{R['opsr']})/('API vs Self-host'!$B$5*$A{i}/1000)")
        cell.number_format = "#,##0"; cell.font = BLACK
    cell = t.cell(row=i, column=7, value=f"=C{i}/100"); cell.number_format = "#,##0"; cell.font = BLACK
t["A10"] = "Throughput does not move break-even; it decides whether one GPU has the capacity to reach it ('API vs Self-host', column G vs H)."
t["A10"].font = Font(name=F, italic=True)
t.column_dimensions["A"].width = 52
for k in range(2, 6):
    t.column_dimensions[get_column_letter(k)].width = 14
t.column_dimensions["F"].width = 40
t.column_dimensions["G"].width = 22

for sheet in wb.worksheets:
    for row_cells in sheet.iter_rows():
        for cell in row_cells:
            if cell.font is None or cell.font.name != F:
                cell.font = Font(name=F, bold=cell.font.bold if cell.font else False,
                                 italic=cell.font.italic if cell.font else False,
                                 color=cell.font.color if cell.font else None, size=cell.font.size if cell.font else 11)

wb.save("model/serving_cost_pricing.xlsx")
print("saved")
