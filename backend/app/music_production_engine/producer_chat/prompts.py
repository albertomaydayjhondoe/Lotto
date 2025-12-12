"""Producer Chat Prompt Templates

Centralized prompt engineering for ChatGPT-5 producer interactions.
All prompts are optimized for creative direction, technical accuracy,
and iterative refinement workflows.
"""

from typing import Dict, List, Optional


def get_system_prompt() -> str:
    """
    Core system prompt defining AI producer persona.
    
    Establishes expertise, communication style, and creative philosophy.
    """
    return """You are an expert music producer with 20+ years experience in hip-hop, trap, and urban music.

Your expertise includes:
- Beat production and arrangement
- Vocal direction and performance coaching
- Lyrical structure and flow optimization
- Mix and mastering guidance
- Industry trends and commercial viability
- Artist development and creative direction

Communication style:
- Direct and honest feedback
- Technical precision balanced with accessibility
- Encouraging but realistic about improvements needed
- Focus on actionable, specific suggestions

Your goal is to help the artist create their best work through:
1. Understanding their creative vision
2. Providing expert technical guidance
3. Iterating toward excellence
4. Maintaining artistic authenticity while maximizing commercial potential

Always consider: energy, flow, structure, production quality, lyrical content, and market positioning."""


def get_aesthetic_definition_prompt(user_input: str) -> str:
    """
    Extract and define musical aesthetic from user description.
    
    Args:
        user_input: Artist's description of desired sound/style
        
    Returns:
        Formatted prompt for aesthetic analysis
    """
    return f"""Based on this artist input:
"{user_input}"

Define the musical aesthetic with these parameters:
1. Genre/subgenre classification
2. Energy level (1-10 scale)
3. Mood/emotional tone
4. Key sonic characteristics
5. Reference artists/tracks
6. Production style (minimal/layered/experimental)
7. Vocal treatment preferences

Provide a concise summary suitable for guiding music generation."""


def get_suno_generation_prompt(context: Dict) -> str:
    """
    Format context into optimized Suno API prompt.
    
    Args:
        context: Creative context from conversation
        
    Returns:
        Suno-formatted generation prompt
    """
    aesthetic = context.get("aesthetic", "modern trap")
    energy = context.get("energy_level", 7)
    tone = context.get("tone", "confident")
    influences = context.get("influences", [])
    structure = context.get("structure", "verse-hook-verse-hook")
    
    influences_str = ", ".join(influences[:3]) if influences else "contemporary urban"
    
    return f"""[GENRE: {aesthetic}]
[ENERGY: {energy}/10]
[MOOD: {tone}]
[INFLUENCES: {influences_str}]
[STRUCTURE: {structure}]
[BPM: auto-detect optimal]
[KEY: auto-detect optimal]
[PRODUCTION: modern, clean, punchy]
[VOCALS: clear, centered, professional]
[MIX: balanced, radio-ready]"""


def get_correction_prompt(analysis_results: Dict) -> str:
    """
    Generate improvement suggestions from analysis results.
    
    Args:
        analysis_results: Combined output from all analysis engines
        
    Returns:
        Structured correction guidance
    """
    audio_score = analysis_results.get("audio_analysis", {}).get("overall_score", 75)
    lyric_issues = analysis_results.get("lyric_analysis", {}).get("issues", [])
    flow_score = analysis_results.get("flow_analysis", {}).get("complexity_score", 70)
    
    return f"""Analysis Results Review:

Audio Quality: {audio_score}/100
Flow Complexity: {flow_score}/100
Identified Issues: {len(lyric_issues)} items

Provide specific, actionable corrections for:
1. Production elements needing adjustment
2. Lyrical improvements (rhyme, metaphor, clarity)
3. Flow and delivery optimization
4. Structural recommendations
5. Mix balance suggestions

Priority: Focus on highest-impact improvements first.
Format: Specific changes with before/after examples where applicable."""


def get_lyric_refinement_prompt(lyrics: str, issues: List[str]) -> str:
    """
    Generate prompt for lyric correction and enhancement.
    
    Args:
        lyrics: Original lyric text
        issues: List of identified problems
        
    Returns:
        Lyric refinement prompt
    """
    issues_formatted = "\n".join(f"- {issue}" for issue in issues)
    
    return f"""Original Lyrics:
{lyrics}

Identified Issues:
{issues_formatted}

Refine the lyrics while:
1. Maintaining the artist's voice and style
2. Preserving core message and intent
3. Improving technical execution (rhyme, meter, flow)
4. Enhancing imagery and word choice
5. Ensuring cultural authenticity

Provide:
- Line-by-line improvements with explanations
- Alternative phrasings where relevant
- Rhyme scheme optimization
- Flow adjustment suggestions

Keep the essence, elevate the execution."""


def get_flow_analysis_prompt(lyrics: str, audio_metadata: Dict) -> str:
    """
    Analyze flow alignment between lyrics and audio.
    
    Args:
        lyrics: Lyric text
        audio_metadata: BPM, rhythm analysis from audio engine
        
    Returns:
        Flow analysis prompt
    """
    bpm = audio_metadata.get("bpm", 140)
    time_signature = audio_metadata.get("time_signature", "4/4")
    
    return f"""Analyze flow for:

Lyrics: {lyrics}
BPM: {bpm}
Time Signature: {time_signature}

Evaluate:
1. Syllable density per bar
2. Rhythmic variation and patterns
3. Breath placement and phrasing
4. Emphasis on key words
5. Syncopation and timing
6. Match with instrumental rhythm

Provide:
- Flow complexity score (1-10)
- Strengths and weaknesses
- Specific sections needing adjustment
- Suggested delivery modifications"""


def get_hit_potential_prompt(all_analyses: Dict) -> str:
    """
    Assess commercial hit potential from all analysis data.
    
    Args:
        all_analyses: Combined results from all engines
        
    Returns:
        Hit potential assessment prompt
    """
    return f"""Hit Potential Assessment:

Audio Analysis: {all_analyses.get('audio', {}).get('overall_score', 0)}/100
Lyric Quality: {all_analyses.get('lyrics', {}).get('quality_score', 0)}/100
Flow Execution: {all_analyses.get('flow', {}).get('complexity_score', 0)}/100
Trend Alignment: {all_analyses.get('trends', {}).get('alignment_score', 0)}/100

Evaluate:
1. Commercial viability (mainstream vs niche)
2. Playlist potential (mood, energy, timing)
3. Viral potential (hooks, memorable moments)
4. Longevity vs trendy
5. Target audience fit
6. Marketing angle strength

Provide:
- Overall hit probability (%)
- Key strengths to leverage
- Critical improvements needed
- Release strategy recommendations
- Positioning advice"""


def get_iteration_feedback_prompt(
    previous_version: Dict,
    current_version: Dict,
    iteration_count: int
) -> str:
    """
    Compare versions and guide next iteration.
    
    Args:
        previous_version: Previous iteration analysis
        current_version: Current iteration analysis
        iteration_count: Current iteration number
        
    Returns:
        Iteration guidance prompt
    """
    return f"""Iteration {iteration_count} Comparison:

Previous Score: {previous_version.get('overall_score', 0)}/100
Current Score: {current_version.get('overall_score', 0)}/100
Improvement: {current_version.get('overall_score', 0) - previous_version.get('overall_score', 0):+d} points

Analyze:
1. What improved?
2. What regressed?
3. What still needs work?
4. Are we on the right track?
5. Should we continue iterating or lock this version?

Next steps:
- If score > 85 and artist satisfied: recommend finalization
- If improving consistently: suggest 1-2 more targeted iterations
- If plateauing: recommend different approach or accept current version
- If regressing: recommend reverting to previous version"""


# Prompt templates library
PROMPT_TEMPLATES = {
    "system": get_system_prompt,
    "aesthetic": get_aesthetic_definition_prompt,
    "suno": get_suno_generation_prompt,
    "correction": get_correction_prompt,
    "lyric_refinement": get_lyric_refinement_prompt,
    "flow_analysis": get_flow_analysis_prompt,
    "hit_potential": get_hit_potential_prompt,
    "iteration_feedback": get_iteration_feedback_prompt,
}


def get_prompt(template_name: str, **kwargs) -> str:
    """
    Retrieve and format prompt template.
    
    Args:
        template_name: Name of template from PROMPT_TEMPLATES
        **kwargs: Template-specific parameters
        
    Returns:
        Formatted prompt string
        
    Raises:
        KeyError: If template_name not found
    """
    if template_name not in PROMPT_TEMPLATES:
        raise KeyError(f"Prompt template '{template_name}' not found")
    
    template_func = PROMPT_TEMPLATES[template_name]
    return template_func(**kwargs)
