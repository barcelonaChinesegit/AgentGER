"""Prompt templates aligned with the AgentGER paper."""

SCORING_DIMENSIONS = """[Scoring Dimension Definitions]
1. Faithfulness:
   Ensure the summary strictly adheres to the figure's facts, including values, trends, proportions, labels, and visual evidence. Do not fabricate, distort, or misinterpret information.
   - 0: The summary severely deviates from the figure's facts, with unsupported claims or fabricated content.
   - 1: The summary is largely consistent with the figure, but contains partial deviations, omissions, or inaccurate details.
   - 2: The summary is fully faithful to the figure, with all key factual information correct.

2. Completeness:
   Check whether the summary covers the main visual elements, trends, comparisons, and key findings in the figure.
   - 0: Misses major content or key information.
   - 1: Covers the main information but has secondary omissions.
   - 2: Fully covers the key information needed to understand the figure.

3. Conciseness:
   Check whether the summary expresses necessary information clearly without redundancy or irrelevant content.
   - 0: Redundant, unfocused, or too brief to communicate key information.
   - 1: Generally concise but could be further tightened.
   - 2: Compact, information-dense, and free of unnecessary wording.

4. Logicality:
   Check whether the summary is coherent, well organized, and free from contradictions or confusing order.
   - 0: Logically confused or self-contradictory.
   - 1: Mostly coherent but with minor jumps, ambiguity, or weak organization.
   - 2: Clear, coherent, and logically organized.

5. Analysis:
   Check whether the summary goes beyond surface description and provides meaningful interpretation of trends, relationships, or implications.
   - 0: Lacks analytical depth or uses inappropriate terminology.
   - 1: Provides limited interpretation or only shallow analysis.
   - 2: Uses appropriate terminology and provides meaningful analytical insight."""


QUALITY_PROMPTS = {
    "low": f"""Analyze this figure and generate a LOW-quality figure summary.

{SCORING_DIMENSIONS}

The summary should be brief, incomplete, and likely to miss important details, specific values, trends, or analytical insight. Keep it to 1-2 short sentences.""",
    "medium": f"""Analyze this figure and generate a MEDIUM-quality figure summary.

{SCORING_DIMENSIONS}

The summary should cover the main idea but may miss precise values, detailed comparisons, or deeper analysis. Keep it to 2-3 sentences.""",
    "high": f"""Analyze this figure and generate a HIGH-quality figure summary.

{SCORING_DIMENSIONS}

The summary should faithfully and concisely cover key visual elements, trends, comparisons, and meaningful analytical insight. Keep it to 3-4 sentences.""",
}


EVA_PROMPT = """You are EvaModel in the AgentGER framework. Your task is fine-grained, human-aligned evaluation of a figure summary.

Given the figure image and the original summary, evaluate the summary across five dimensions using the discrete score set {{0, 1, 2}}. For each dimension, first provide a concise reasoning chain grounded in the visible figure-summary relationship, then assign the score.

{scoring_dimensions}

---

[Original Summary]
{summary}

---

[Output Requirements]
Return valid JSON inside <evaluation> tags with exactly this schema:

<evaluation>
{{"scores": {{"faithfulness": 0-2, "completeness": 0-2, "conciseness": 0-2, "logicality": 0-2, "analysis": 0-2}}, "reasons": {{"faithfulness": "reasoning grounded in the figure", "completeness": "reasoning grounded in the figure", "conciseness": "reasoning grounded in the figure", "logicality": "reasoning grounded in the figure", "analysis": "reasoning grounded in the figure"}}}}
</evaluation>

Do not output weights or an overall weighted score."""


REF_PROMPT = """You are RefModel in the AgentGER framework. Your task is evaluation-guided refinement of a figure summary.

Given the figure image and the original summary, first evaluate the summary across five dimensions using the discrete score set {{0, 1, 2}}. For each dimension, provide a concise reasoning chain before the score. Then generate an improved summary that fixes low-scoring dimensions while preserving correct high-scoring content.

{scoring_dimensions}

Refinement guidance:
- If Faithfulness is low, correct factual errors and unsupported claims.
- If Completeness is low, add missing trends, comparisons, values, or key findings.
- If Conciseness is low, remove redundancy and keep the summary focused.
- If Logicality is low, reorganize the summary into a clear, coherent order.
- If Analysis is low, add meaningful interpretation grounded in the figure.

---

[Original Summary]
{summary}

---

[Output Requirements]
Return valid JSON in two tagged blocks:

<evaluation>
{{"scores": {{"faithfulness": 0-2, "completeness": 0-2, "conciseness": 0-2, "logicality": 0-2, "analysis": 0-2}}, "reasons": {{"faithfulness": "reasoning grounded in the figure", "completeness": "reasoning grounded in the figure", "conciseness": "reasoning grounded in the figure", "logicality": "reasoning grounded in the figure", "analysis": "reasoning grounded in the figure"}}}}
</evaluation>
<modification>
{{"improved_summary": "refined figure summary"}}
</modification>

Do not output weights or an overall weighted score."""


def build_eva_prompt(summary: str) -> str:
    """Build the EvaModel Chain-of-Evaluation prompt."""
    return EVA_PROMPT.format(scoring_dimensions=SCORING_DIMENSIONS, summary=summary)


def build_ref_prompt(summary: str) -> str:
    """Build the RefModel evaluation-guided refinement prompt."""
    return REF_PROMPT.format(scoring_dimensions=SCORING_DIMENSIONS, summary=summary)
