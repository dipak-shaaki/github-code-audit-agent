import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Preformatted, HRFlowable, Table, TableStyle
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import PageBreak
from pygments.lexers import PythonLexer, get_lexer_by_name, TextLexer
from pygments.formatter import Formatter
from pygments.token import Token
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ─── Color Palette (VS Code inspired) ────────────────────────────────────────
DARK_BG = colors.HexColor("#1e1e1e")
CODE_BG = colors.HexColor("#1e1e1e")
CODE_FG = colors.HexColor("#d4d4d4")
HEADER_COLOR = colors.HexColor("#2c3e50")
ACCENT = colors.HexColor("#3498db")
HIGH_RISK = colors.HexColor("#e74c3c")
MEDIUM_RISK = colors.HexColor("#f39c12")
LOW_RISK = colors.HexColor("#27ae60")
LIGHT_GREY = colors.HexColor("#f5f5f5")
BORDER_COLOR = colors.HexColor("#dedede")
TEXT_COLOR = colors.HexColor("#2c2c2c")


# ─── ReportLab Pygments Formatter ────────────────────────────────────────────
class ReportLabFormatter(Formatter):
    """
    Converts pygments syntax tokens into ReportLab color values.
    Maps each token type (keyword, string, comment etc) to a VS Code color.
    Used by render_code_block() to colorize code.
    """

    TOKEN_COLORS = {
        Token.Keyword: colors.HexColor("#569cd6"),
        Token.Keyword.Import: colors.HexColor("#569cd6"),
        Token.Keyword.Namespace: colors.HexColor("#569cd6"),
        Token.Name.Function: colors.HexColor("#dcdcaa"),
        Token.Name.Class: colors.HexColor("#4ec9b0"),
        Token.Name.Builtin: colors.HexColor("#4ec9b0"),
        Token.Name.Decorator: colors.HexColor("#c586c0"),
        Token.String: colors.HexColor("#ce9178"),
        Token.String.Double: colors.HexColor("#ce9178"),
        Token.String.Single: colors.HexColor("#ce9178"),
        Token.Comment: colors.HexColor("#6a9955"),
        Token.Comment.Single: colors.HexColor("#6a9955"),
        Token.Number: colors.HexColor("#b5cea8"),
        Token.Operator: colors.HexColor("#d4d4d4"),
        Token.Punctuation: colors.HexColor("#d4d4d4"),
        Token.Name.Builtin.Pseudo: colors.HexColor("#569cd6"),
    }
    DEFAULT_COLOR = colors.HexColor("#d4d4d4")

    def get_color(self, token_type):
        """Walk up token hierarchy to find closest matching color."""
        while token_type:
            if token_type in self.TOKEN_COLORS:
                return self.TOKEN_COLORS[token_type]
            token_type = token_type.parent
        return self.DEFAULT_COLOR


# ─── Build Text Styles ────────────────────────────────────────────────────────
def build_styles():
    """
    Defines all text styles used in the PDF.
    Uses Times-Roman for body text (professional look).
    Uses Courier for code blocks (monospace).
    Returns a dict of named ParagraphStyle objects.
    """
    return {
        "h1": ParagraphStyle(
            "h1",
            fontSize=20,
            fontName="Times-Bold",
            textColor=HEADER_COLOR,
            spaceBefore=18,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontSize=15,
            fontName="Times-Bold",
            textColor=HEADER_COLOR,
            spaceBefore=14,
            spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "h3",
            fontSize=11,
            fontName="Times-Bold",
            textColor=colors.HexColor("#444444"),
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            fontSize=10,
            fontName="Times-Roman",
            textColor=TEXT_COLOR,
            spaceAfter=6,
            leading=16,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontSize=10,
            fontName="Times-Roman",
            textColor=TEXT_COLOR,
            spaceAfter=4,
            leftIndent=20,
            leading=15,
        ),
        "code_fallback": ParagraphStyle(
            "code_fallback",
            fontSize=8.5,
            fontName="Courier",
            textColor=colors.HexColor("#1a1a1a"),
            backColor=colors.HexColor("#f5f5f5"),
            spaceAfter=8,
            spaceBefore=4,
            leftIndent=10,
            rightIndent=10,
            leading=13,
            borderPad=8,
            borderColor=colors.HexColor("#cccccc"),
            borderWidth=1,
        ),
    }


# ─── Title Page ───────────────────────────────────────────────────────────────
def add_title_page(story, repo_name, pr_number, risk_level):
    """
    Builds the cover page of the PDF.
    Shows:
    - Dark blue header with report title
    - Metadata table: repo name, PR number, risk level
    - Risk level text is colored RED/ORANGE/GREEN based on severity
    """
    risk_color = {
        "HIGH": HIGH_RISK,
        "MEDIUM": MEDIUM_RISK,
        "LOW": LOW_RISK,
    }.get(risk_level, colors.grey)

    # dark header block
    report_title = "Repository Audit Report" if str(pr_number) == "full_scan" else "PR Audit Report"
    title_data = [[
    Paragraph(report_title, ParagraphStyle(
            "tp", fontSize=26, fontName="Times-Bold",
            textColor=colors.white, alignment=TA_CENTER
        ))
    ]]
    title_table = Table(title_data, colWidths=[6.5 * inch])
    title_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HEADER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 30),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 30),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
    ]))
    story.append(title_table)
    story.append(Spacer(1, 20))

    # metadata table
    scan_label = "Full Repository Scan" if str(pr_number) == "full_scan" else f"#{pr_number}"
    meta_data = [
    ["Repository", repo_name],
    ["Scan", scan_label],
    ["Risk Level", risk_level],
]

    meta_table = Table(meta_data, colWidths=[2 * inch, 4.5 * inch])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_GREY),
        ("FONTNAME", (0, 0), (0, -1), "Times-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("TEXTCOLOR", (1, 2), (1, 2), risk_color),
        ("FONTNAME", (1, 2), (1, 2), "Times-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 30))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR))
    story.append(Spacer(1, 20))

def render_code_block(code_text, language="python"):
    """
    Renders a code block with VS Code dark theme syntax highlighting.
    Steps:
    1. Use pygments to tokenize the code by language
    2. Map each token to a VS Code color using ReportLabFormatter
    3. Build one Paragraph per line with colored font spans
    4. Wrap all lines in a dark background Table with border
    Falls back to plain grey code block if anything fails.
    """
    from reportlab.platypus import Table, TableStyle as TS

    try:
        # pick lexer by language
        if language == "python":
            lexer = PythonLexer()
        else:
            try:
                lexer = get_lexer_by_name(language)
            except:
                lexer = TextLexer()

        formatter = ReportLabFormatter()
        tokens = list(lexer.get_tokens(code_text))

        # split tokens into lines
        lines = []
        current_line = []

        for token_type, value in tokens:
            color = formatter.get_color(token_type)
            parts = value.split("\n")
            for i, part in enumerate(parts):
                if part:
                    current_line.append((part, color))
                if i < len(parts) - 1:
                    lines.append(current_line)
                    current_line = []

        if current_line:
            lines.append(current_line)

        # style for each code line
        code_line_style = ParagraphStyle(
            "code_line",
            fontSize=8.5,
            fontName="Courier",
            textColor=colors.HexColor("#d4d4d4"),
            backColor=colors.HexColor("#1e1e1e"),
            leading=14,
            leftIndent=0,
            rightIndent=0,
        )

        # build colored paragraph per line
        line_paragraphs = []
        for line in lines:
            if not line:
                line_paragraphs.append(Paragraph("&nbsp;", code_line_style))
                continue

            xml_parts = []
            for text, clr in line:
                text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                # get hex string from color object
                if hasattr(clr, 'hexval'):
                    hex_color = clr.hexval()
                elif hasattr(clr, 'red'):
                    hex_color = "#{:02x}{:02x}{:02x}".format(
                        int(clr.red * 255),
                        int(clr.green * 255),
                        int(clr.blue * 255)
                    )
                else:
                    hex_color = "#d4d4d4"
                xml_parts.append(
                    f'<font name="Courier" color="{hex_color}">{text}</font>'
                )

            xml = "".join(xml_parts)
            line_paragraphs.append(Paragraph(xml, code_line_style))

        # wrap in dark bordered table
        table_data = [[p] for p in line_paragraphs]
        table = Table(table_data, colWidths=[6 * inch])
        table.setStyle(TS([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1e1e1e")),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("LINEABOVE", (0, 0), (-1, 0), 1, colors.HexColor("#3c3c3c")),
            ("LINEBELOW", (0, -1), (-1, -1), 1, colors.HexColor("#3c3c3c")),
            ("LINEBEFORE", (0, 0), (0, -1), 1, colors.HexColor("#3c3c3c")),
            ("LINEAFTER", (-1, 0), (-1, -1), 1, colors.HexColor("#3c3c3c")),
        ]))
        return table

    except Exception as e:
        # fallback — plain light code block
        return Preformatted(code_text, ParagraphStyle(
            "code_fallback",
            fontSize=8.5,
            fontName="Courier",
            textColor=colors.HexColor("#1a1a1a"),
            backColor=colors.HexColor("#f5f5f5"),
            leading=13,
            leftIndent=10,
            rightIndent=10,
            borderColor=colors.HexColor("#cccccc"),
            borderWidth=1,
            borderPad=8,
        ))


# ─── Clean Markdown Text ──────────────────────────────────────────────────────
def clean_text(text):
    """
    Converts markdown formatting to ReportLab XML tags.
    - Escapes & < > to avoid XML parse errors
    - **bold** -> <b>bold</b>
    - *italic* -> <i>italic</i>
    - `inline code` -> Courier font span
    """
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'`(.+?)`', r'<font name="Courier" size="9">\1</font>', text)
    return text


# ─── Markdown Parser ──────────────────────────────────────────────────────────
def parse_markdown_to_pdf(content, story, styles):
    """
    Reads LLM-generated markdown line by line.
    Converts each line to the correct ReportLab element:
    - # -> h1 with accent lines
    - ## -> h2 with short accent line
    - ### -> h3
    - ``` -> VS Code syntax highlighted code block
    - - or * -> bullet point
    - 1. -> numbered list
    - --- -> horizontal rule
    - everything else -> body paragraph
    """
    in_code_block = False
    code_lines = []
    current_lang = "python"

    for line in content.split("\n"):

        # detect code block start/end
        if line.strip().startswith("```"):
            if in_code_block:
                # end of code block — render with syntax highlighting
                code_text = "\n".join(code_lines)
                if code_text.strip():
                    story.append(Spacer(1, 6))
                    story.append(render_code_block(code_text, current_lang))
                    story.append(Spacer(1, 6))
                code_lines = []
                in_code_block = False
                current_lang = "python"
            else:
                # start of code block — detect language
                lang_hint = line.strip()[3:].strip().lower()
                current_lang = lang_hint if lang_hint else "python"
                in_code_block = True
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        stripped = line.strip()

        if stripped.startswith("# "):
            story.append(Spacer(1, 8))
            story.append(HRFlowable(width="100%", thickness=2, color=ACCENT))
            story.append(Spacer(1, 4))
            story.append(Paragraph(stripped[2:], styles["h1"]))
            story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR))
            story.append(Spacer(1, 4))

        elif stripped.startswith("## "):
            story.append(Spacer(1, 8))
            story.append(Paragraph(stripped[3:], styles["h2"]))
            story.append(HRFlowable(width="60%", thickness=0.5, color=ACCENT))
            story.append(Spacer(1, 4))

        elif stripped.startswith("### "):
            story.append(Spacer(1, 4))
            story.append(Paragraph(stripped[4:], styles["h3"]))

        elif stripped.startswith("#### "):
            story.append(Paragraph(stripped[5:], styles["h3"]))

        elif stripped.startswith("- ") or stripped.startswith("* "):
            text = clean_text(stripped[2:])
            story.append(Paragraph(f"• {text}", styles["bullet"]))

        elif len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in ".):":
            text = clean_text(stripped[2:].strip())
            story.append(Paragraph(f"{stripped[0]}. {text}", styles["bullet"]))

        elif stripped in ["---", "***", "___"]:
            story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR))
            story.append(Spacer(1, 4))

        elif stripped == "":
            story.append(Spacer(1, 4))

        else:
            text = clean_text(stripped)
            if text:
                story.append(Paragraph(text, styles["body"]))


# ─── Save Report ──────────────────────────────────────────────────────────────
def save_report(repo_name, pr_number, content, risk_level="UNKNOWN"):
    """
    Saves the report in two formats:
    1. Markdown .md file — raw LLM output
    2. PDF file — fully formatted with title page, styled sections, code blocks
    Returns the PDF path so Slack can upload it.
    """
    os.makedirs("reports", exist_ok=True)

    md_filename = f"reports/{repo_name.replace('/', '_')}_pr_{pr_number}.md"
    with open(md_filename, "w") as f:
        f.write(content)
    print(f"Report saved to {md_filename}")

    pdf_filename = f"reports/{repo_name.replace('/', '_')}_pr_{pr_number}.pdf"
    _build_pdf(content, pdf_filename, repo_name, pr_number, risk_level)
    print(f"PDF saved to {pdf_filename}")

    return pdf_filename


# ─── Build PDF ────────────────────────────────────────────────────────────────
def _build_pdf(content, filename, repo_name, pr_number, risk_level):
    """
    Assembles the full PDF document.
    1. Creates SimpleDocTemplate with A4 page size and margins
    2. Builds styles
    3. Adds title page
    4. Parses markdown content into styled elements
    5. Calls doc.build() to render everything to file
    """
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=1.2 * cm + 0.5 * inch,
        leftMargin=1.2 * cm + 0.5 * inch,
        topMargin=inch,
        bottomMargin=inch
    )

    styles = build_styles()
    story = []

    add_title_page(story, repo_name, pr_number, risk_level)
    parse_markdown_to_pdf(content, story, styles)

    doc.build(story)