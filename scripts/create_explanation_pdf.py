"""Create a submission-ready explanation PDF from the generated assignment results."""
from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "SynergyLabs_Assignment_Explanation_and_Tech_Stack.pdf"
PAGE_WIDTH, PAGE_HEIGHT = A4

NAVY = colors.HexColor("#12355B")
BLUE = colors.HexColor("#1D70B8")
TEAL = colors.HexColor("#157A6E")
LIGHT_BLUE = colors.HexColor("#EAF3FB")
LIGHT_TEAL = colors.HexColor("#E8F5F1")
LIGHT_GREY = colors.HexColor("#F4F6F8")
MID_GREY = colors.HexColor("#5D6975")
DARK = colors.HexColor("#17212B")
WHITE = colors.white


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=26, leading=31,
                                textColor=NAVY, alignment=TA_CENTER, spaceAfter=8),
        "subtitle": ParagraphStyle("subtitle", parent=base["Normal"], fontName="Helvetica", fontSize=12.5, leading=18,
                                   textColor=MID_GREY, alignment=TA_CENTER, spaceAfter=18),
        "kicker": ParagraphStyle("kicker", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=9, leading=12,
                                  textColor=BLUE, alignment=TA_CENTER, spaceAfter=12),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=18, leading=23,
                              textColor=NAVY, spaceBefore=0, spaceAfter=9),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=12.5, leading=16,
                              textColor=NAVY, spaceBefore=8, spaceAfter=5),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.6, leading=14,
                                textColor=DARK, spaceAfter=6),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontName="Helvetica", fontSize=8, leading=11,
                                 textColor=MID_GREY),
        "card_title": ParagraphStyle("card_title", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10.5,
                                      leading=13, textColor=NAVY, spaceAfter=4),
        "card_body": ParagraphStyle("card_body", parent=base["Normal"], fontName="Helvetica", fontSize=8.8,
                                     leading=12.5, textColor=DARK),
        "flow": ParagraphStyle("flow", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8.2, leading=10.5,
                                textColor=WHITE, alignment=TA_CENTER),
        "metric": ParagraphStyle("metric", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=18, leading=21,
                                  textColor=TEAL, alignment=TA_CENTER),
        "metric_label": ParagraphStyle("metric_label", parent=base["Normal"], fontName="Helvetica", fontSize=7.9,
                                        leading=10, textColor=MID_GREY, alignment=TA_CENTER),
        "table_head": ParagraphStyle("table_head", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8,
                                      leading=10, textColor=WHITE),
        "table_cell": ParagraphStyle("table_cell", parent=base["Normal"], fontName="Helvetica", fontSize=8,
                                      leading=10.5, textColor=DARK),
    }


S = styles()


def p(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, S[style])


def bullet(text: str) -> Paragraph:
    return Paragraph(f'<font color="#1D70B8">-</font> {text}', S["body"])


def card(title: str, body: str, tint=LIGHT_BLUE) -> Table:
    content = [[p(title, "card_title")], [p(body, "card_body")]]
    result = Table(content, colWidths=[82 * mm])
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), tint),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#C8DCEB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return result


def metric(value: str, label: str) -> Table:
    result = Table([[p(value, "metric")], [p(label, "metric_label")]], colWidths=[41 * mm])
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_TEAL),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#B9DED6")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return result


def flow(nodes: list[str], color: colors.Color) -> Table:
    cells = [[p(item, "flow") for item in nodes]]
    widths = [168 * mm / len(nodes)] * len(nodes)
    result = Table(cells, colWidths=widths)
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#FFFFFF")),
        ("INNERGRID", (0, 0), (-1, -1), 0.7, WHITE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    return result


def section_banner(number: str, title: str, subtitle: str) -> list:
    return [
        p(number, "kicker"),
        p(title, "h1"),
        p(subtitle, "body"),
    ]


def footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D7E0E8"))
    canvas.line(21 * mm, 15 * mm, PAGE_WIDTH - 21 * mm, 15 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MID_GREY)
    canvas.drawString(21 * mm, 10 * mm, "SynergyLabs Applied AI / ML Engineering Take-Home")
    canvas.drawRightString(PAGE_WIDTH - 21 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf() -> Path:
    rag = read_json("problem1_cost_efficient_rag/results/eval_results.json")
    judge = read_json("problem2_llm_as_judge/results/suite_report.json")
    rag_m = rag["retrieval_metrics"]
    answer_m = rag["answer_metrics"]
    latency = rag["latency_ms"]
    suite = judge["suite"]
    validation = judge["validation"]
    probes = judge["adversarial_probes"]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=21 * mm, leftMargin=21 * mm,
                            topMargin=19 * mm, bottomMargin=21 * mm, title="SynergyLabs Assignment Explanation and Tech Stack")
    story: list = []

    # Cover
    story.extend([
        Spacer(1, 30 * mm),
        p("APPLIED AI / ML ENGINEERING", "kicker"),
        p("SynergyLabs Assignment", "title"),
        p("Implementation explanation, scenarios, and technology rationale", "subtitle"),
        Spacer(1, 9 * mm),
        flow(["Problem 1\nCost-Efficient RAG", "Problem 2\nLLM-as-Judge"], NAVY),
        Spacer(1, 15 * mm),
        p("What this document covers", "h2"),
        bullet("The business problem each component solves and the end-to-end execution scenario."),
        bullet("Why the chosen Python, sqlite-vec, FastAPI, structured-schema, and evaluation tools fit the assignment."),
        bullet("The generated retrieval, cost, bias, and validation evidence included with the project."),
        Spacer(1, 16 * mm),
        Table([[card("Offline-first demonstration", "The submitted sample runs without an API key. OpenAI is optional and configured only through environment variables.", LIGHT_TEAL),
                card("Honest scope", "The included metrics come from a small fixed test corpus. Cost at 100K to 10M vectors is an explicit planning model, not a vendor quote.", LIGHT_GREY)]], colWidths=[84 * mm, 84 * mm], hAlign="CENTER"),
    ])
    story.append(PageBreak())

    # Problem 1 scenario
    story.extend(section_banner("PROBLEM 1", "Cost-Efficient RAG Application", "Scenario: a support team needs trustworthy answers across product, security, release, SLA, retention, and integration documents without paying for an always-on managed vector database."))
    story.append(flow(["PDF / HTML / MD", "Extract + chunk", "SHA-256 dedupe", "384d embedding", "sqlite-vec search", "Cited answer"], BLUE))
    story.extend([
        Spacer(1, 6 * mm),
        p("How the scenario runs", "h2"),
        bullet("An administrator sends local files to <b>POST /ingest</b>. The pipeline extracts text, splits it into configurable 450-character chunks with 60-character overlap, assigns metadata, and hashes every chunk."),
        bullet("The same document can be ingested again safely. The chunk hash is the SQLite primary key, so an existing vector is skipped instead of duplicated."),
        bullet("A user asks, for example, <i>What encryption protects customer data at rest?</i>. The service embeds the query, searches sqlite-vec, applies an optional metadata filter such as <i>category=security</i>, and returns a citation-backed answer."),
        bullet("If the best context is below the configured relevance threshold, the API returns the explicit no-context response rather than inventing an answer."),
        p("Why this architecture", "h2"),
        Table([
            [card("Low idle cost", "sqlite-vec runs inside a local SQLite file. There is no separate server or permanently allocated vector pod while the app is stopped."),
             card("Grounded answers", "The answer prompt is restricted to retrieved text and requires document/chunk citations. This makes evidence inspectable by the caller.")],
            [card("Practical retrieval", "The store uses vector candidate selection plus a lexical re-ranker, reducing the chance that a small hashing-vector collision outranks direct evidence.", LIGHT_TEAL),
             card("Traceable operations", "Each query logs retrieval and generation latency, retrieved chunk count, tokens, provider, and filter to JSON Lines.", LIGHT_TEAL)],
        ], colWidths=[84 * mm, 84 * mm], hAlign="CENTER"),
    ])
    story.append(PageBreak())

    # Problem 1 evidence and stack
    story.extend(section_banner("PROBLEM 1", "Evidence and technology rationale", "The included 18-question benchmark covers factual questions from a fixed sample corpus. Retrieval and answer measurements are generated by the supplied evaluation harness."))
    story.append(Table([[metric(f"{rag_m['recall_at_3']:.0%}", "Recall@3"), metric(f"{rag_m['mrr']:.3f}", "MRR"),
                         metric(f"{rag_m['ndcg_at_3']:.3f}", "nDCG@3"), metric(f"{latency['retrieval_p50']:.1f} ms", "Retrieval p50")]],
                       colWidths=[42 * mm] * 4, hAlign="CENTER"))
    story.extend([
        Spacer(1, 5 * mm),
        p("Evaluation highlights", "h2"),
        bullet(f"Idempotence was observed: first ingest inserted {rag['ingestion_idempotence']['first_run']['inserted_chunks']} chunks; second ingest inserted {rag['ingestion_idempotence']['second_run']['inserted_chunks']} and skipped {rag['ingestion_idempotence']['second_run']['skipped_existing_chunks']} existing chunks."),
        bullet(f"Answer evidence: {answer_m['faithfulness_citation_lexical']:.0%} citation/lexical faithfulness, {answer_m['exact_match_contains_gold']:.0%} exact-match containment, and {answer_m['answer_relevance_lexical']:.3f} lexical answer relevance."),
        bullet(f"Latency: p50 {latency['retrieval_p50']:.3f} ms and p95 {latency['retrieval_p95']:.3f} ms on the bundled local corpus. These are local-demo values, not a distributed production benchmark."),
        p("Cost model", "h2"),
        Table([
            [p("Vectors", "table_head"), p("Embedded sqlite-vec", "table_head"), p("Managed DB assumption", "table_head"), p("Estimated savings", "table_head")],
            [p("100K", "table_cell"), p("$25.02 / month", "table_cell"), p("$70 / month", "table_cell"), p("64.3%", "table_cell")],
            [p("1M", "table_cell"), p("$25.20 / month", "table_cell"), p("$280 / month", "table_cell"), p("91.0%", "table_cell")],
            [p("10M", "table_cell"), p("$26.96 / month", "table_cell"), p("$1,200 / month", "table_cell"), p("97.8%", "table_cell")],
        ], colWidths=[38 * mm, 45 * mm, 45 * mm, 40 * mm], style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("BACKGROUND", (0, 1), (-1, -1), LIGHT_GREY),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C9D3DC")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])),
        p("Assumptions: 384 float32 dimensions plus 512 bytes metadata/index allowance, 50K queries/month, a $25 shared application VM, disk/backup storage, and illustrative always-on managed pricing. Embedding/generation API spend is excluded because it is store-independent.", "small"),
        p("Stack choices", "h2"),
        bullet("<b>Python + FastAPI + Uvicorn:</b> quick HTTP delivery, typed request validation, and easy local development."),
        bullet("<b>sqlite-vec + SQLite:</b> embedded persistence, metadata indexes, deterministic upserts, and no idle control plane. Move to Qdrant/pgvector/managed service for HA, multi-region, high concurrency, or high-scale throughput."),
        bullet("<b>Hashing 384d embeddings:</b> no download or API key for a reproducible demo. The provider boundary supports an OpenAI model when semantic quality is the priority."),
        bullet("<b>pypdf + BeautifulSoup:</b> lightweight support for PDF, HTML, Markdown, and text without a complex document platform."),
    ])
    story.append(PageBreak())

    # Problem 2 scenario
    story.extend(section_banner("PROBLEM 2", "LLM-as-Judge Evaluation Pipeline", "Scenario: a team wants to decide whether a new prompt or model configuration is better, but cannot trust an unexamined judge because judges can favor first position, verbosity, polished confidence, or their own model family."))
    story.append(flow(["JSON / YAML suite", "Structured rubric", "Judge A vs B", "Swap B vs A", "Aggregate", "Audit + validation"], TEAL))
    story.extend([
        Spacer(1, 6 * mm),
        p("How the scenario runs", "h2"),
        bullet("A test case contains the input, system prompt, expected answer, and outputs from configuration A and B. The judge produces a strict JSON verdict, then Pydantic validates it. Fenced or embedded JSON is repaired/extracted when possible."),
        bullet("Both outputs receive pointwise scores for correctness, faithfulness, completeness, instruction following, tone, and safety. The weighted criteria make the reasoning visible instead of relying on a single opaque number."),
        bullet("For every comparison, the pipeline judges A vs B and then B vs A. The reverse result is mapped back to original labels. If the winner changes, the case is conservatively declared a tie."),
        bullet("Every judge prompt, raw response, parsed result, token estimate, latency, and configuration is appended to an audit log for replay and investigation."),
        p("Bias safeguards implemented", "h2"),
        Table([
            [card("Position bias", "Order-swapped pairs are required. The report includes the per-case consistency flag and flip rate."),
             card("Verbosity and style", "Score anchors and explicit tone rules penalize unsupported padding. Terse-but-correct answers are not penalized merely for being short.")],
            [card("Sycophancy and confidence", "Per-criterion grounding against a reference prevents confident or polished phrasing from masking incorrect claims.", LIGHT_TEAL),
             card("Self-enhancement and clustering", "Generator families are configured separately from the judge, and 1/3/5 calibration anchors encourage use of the full scale.", LIGHT_TEAL)],
        ], colWidths=[84 * mm, 84 * mm], hAlign="CENTER"),
    ])
    story.append(PageBreak())

    # Problem 2 evidence and tech stack
    story.extend(section_banner("PROBLEM 2", "Validation evidence and technology rationale", "The demonstration suite compares two configurations over eight reference-based factual and instruction-following cases, plus adversarial probes."))
    story.append(Table([[metric(f"{suite['config_b']['pass_rate']:.1%}", "Config B pass rate"), metric("8 - 0", "B wins - A wins"),
                         metric(f"{suite['pairwise']['position_flip_rate']:.0%}", "Position flip rate"), metric(f"{probes['probe_accuracy']:.0%}", "Probe accuracy")]],
                       colWidths=[42 * mm] * 4, hAlign="CENTER"))
    story.extend([
        Spacer(1, 5 * mm),
        p("What the report says", "h2"),
        bullet(f"Configuration B is the declared winner. Its mean overall score is {suite['config_b']['mean_overall']:.3f} versus {suite['config_a']['mean_overall']:.3f} for A, with {suite['config_b']['pass_rate']:.1%} versus {suite['config_a']['pass_rate']:.1%} pass rate."),
        bullet(f"The order swap check produced {suite['pairwise']['position_flip_rate']:.0%} flips. Human/gold validation achieved quadratic weighted Cohen's kappa of {validation['quadratic_weighted_cohens_kappa']:.4f} and pairwise winner agreement of {validation['pairwise_winner_agreement']:.0%}."),
        bullet(f"The adversarial suite achieved {probes['probe_accuracy']:.0%}: it rejected verbose/confidently wrong answers, accepted terse correct answers, and limited the padded-correct answer's score."),
        bullet("The default offline judge is deliberately deterministic. Its 100% test-retest result proves repeatable pipeline behavior, not real-world LLM reliability. A production release gate must use a distinct external judge model, more human labels, and human review for high-impact cases."),
        p("Stack choices", "h2"),
        bullet("<b>Pydantic:</b> validates structured verdicts and keeps malformed model output from silently corrupting reports."),
        bullet("<b>JSON + YAML:</b> human-readable suites/rubrics with no database required for a take-home demo; JSON Lines audit records make every call append-only and inspectable."),
        bullet("<b>Provider abstraction:</b> offline scoring makes the project runnable without credentials; an OpenAI judge can be selected with environment variables, independently from generator A/B."),
        bullet("<b>Custom IR and agreement metrics:</b> transparent Recall/MRR/nDCG, pass rates, flip rate, adversarial accuracy, and quadratic weighted kappa avoid hiding evaluation logic behind a black box."),
        p("Final takeaway", "h2"),
        p("The submission prioritizes cost visibility, grounded answers, reproducible evaluations, and auditability. sqlite-vec is a credible low-idle-cost choice for small or lightly queried corpora; the judge pipeline is a useful regression signal only after its bias checks and human agreement are monitored in the environment where it will be used.", "body"),
    ])

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return OUTPUT


if __name__ == "__main__":
    print(build_pdf())
