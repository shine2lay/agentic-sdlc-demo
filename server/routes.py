"""REST API routes."""

from __future__ import annotations

import json
import random
import uuid
from datetime import UTC, datetime
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, func, select

from server.database import get_session
from server.models import Run, RunEvent

router = APIRouter()

SDLC_WORKFLOW = "sdlc_deploy_test"


def calculate_duration(started_at: datetime | None, completed_at: datetime | None) -> float | None:
    """Calculate duration in seconds between started_at and completed_at."""
    if started_at and completed_at:
        return (completed_at - started_at).total_seconds()
    return None


COST_PER_TOKEN = 0.000015  # $15 per million tokens (blended Claude rate)


def extract_total_tokens(result: dict | None) -> int | None:
    """Extract total_tokens from execution result if available."""
    if not result:
        return None
    execution = result.get("execution")
    if execution and isinstance(execution, dict):
        return execution.get("total_tokens")
    return None


def calculate_cost_dollars(total_tokens: int | None) -> float | None:
    """Calculate approximate cost in USD from token count."""
    if total_tokens is None:
        return None
    return round(total_tokens * COST_PER_TOKEN, 4)


def extract_workflow_output(result: dict | None) -> dict | None:
    """Extract workflow_output from execution result if available."""
    if not result:
        return None
    execution = result.get("execution")
    if execution and isinstance(execution, dict):
        return execution.get("workflow_output")
    return None


# ── Request/Response models ───────────────────────────────────────

class CreateRunRequest(BaseModel):
    workflow: str
    inputs: dict[str, Any] = {}


class CreateRunResponse(BaseModel):
    id: str
    status: str = "pending"


class SuggestRequest(BaseModel):
    suggestion: str


class ClaimRequest(BaseModel):
    worker_id: str


class CompleteRequest(BaseModel):
    status: str  # completed | failed
    result: dict[str, Any] | None = None
    error: str | None = None


class TypewriterLine(BaseModel):
    text: str
    css_class: str


class TypewriterConfigResponse(BaseModel):
    enabled: bool
    lines: List[TypewriterLine]
    speed_ms: int
    start_delay_ms: int


class BackToTopConfigResponse(BaseModel):
    enabled: bool
    scroll_threshold_px: int
    position_right_px: int
    position_bottom_px: int
    size_px: int
    bg_color: str
    hover_bg_color: str
    icon_color: str
    border_radius: str
    transition_ms: int
    scroll_behavior: str
    scroll_duration_ms: int
    scroll_easing: str
    respect_reduced_motion: bool


class ParallaxConfigResponse(BaseModel):
    enabled: bool
    speed_factor: float
    max_offset_px: int
    direction: str
    easing: str


class SparkleConfigResponse(BaseModel):
    enabled: bool
    particle_count: int
    duration_ms: int
    spread_px: int
    colors: List[str]
    repeat_interval_ms: int
    size_px: int
    target: str


class GradientBorderConfigResponse(BaseModel):
    enabled: bool
    colors: List[str]
    angle_deg: int
    animation_duration_ms: int
    border_width_px: int
    border_radius: str
    target: str


class TicTacToeConfigResponse(BaseModel):
    board_size: int
    player_symbols: List[str]
    player_colors: List[str]
    winning_length: int
    empty_cell: str
    title: str


class SuggestionsCountResponse(BaseModel):
    total_suggestions: int
    poll_interval_ms: int


class QueueCountResponse(BaseModel):
    queued_runs: int
    poll_interval_ms: int


class MarkdownPreviewConfigResponse(BaseModel):
    title: str
    default_markdown: str
    editor_placeholder: str
    debounce_ms: int


class ColorPickerConfigResponse(BaseModel):
    title: str
    default_color: str
    formats: List[str]
    show_preview: bool
    preset_colors: List[str]


class BounceButtonConfigResponse(BaseModel):
    enabled: bool
    scale_start: float
    scale_peak: float
    duration_ms: int
    easing: str
    iteration_count: int
    delay_ms: int
    debounce_ms: int
    skip_initial_render: bool
    respect_reduced_motion: bool
    target: str


class SuggestionChipBounceConfigResponse(BaseModel):
    enabled: bool
    translate_y_px: float
    duration_ms: int
    easing: str
    stagger_ms: int
    initial_delay_ms: int
    iteration_count: int
    respect_reduced_motion: bool
    target: str


class ConfettiConfigResponse(BaseModel):
    enabled: bool
    particle_count: int
    duration_ms: int
    spread_px: int
    colors: List[str]
    gravity: float
    drift: float
    size_range: List[int]
    shapes: List[str]
    trigger: str
    trigger_from: str
    trigger_to: str
    respect_reduced_motion: bool
    target: str
    max_concurrent: int


class PipelineGlowConfigResponse(BaseModel):
    enabled: bool
    glow_color_rgb: str
    min_blur_px: int
    max_blur_px: int
    min_spread_px: int
    max_spread_px: int
    min_opacity: float
    max_opacity: float
    animation_duration_ms: int
    total_stages: int
    respect_reduced_motion: bool
    target: str


class AsciiArtConfigResponse(BaseModel):
    enabled: bool
    title: str
    default_text: str
    max_length: int
    block_char: str
    empty_char: str
    supported_characters: str
    letter_height: int


class AsciiArtRequest(BaseModel):
    text: str


class AsciiArtResponse(BaseModel):
    art: str
    original_text: str
    width: int
    height: int


class CommunityCreationItem(BaseModel):
    name: str
    description: str
    path: str


class CommunityCreationsConfigResponse(BaseModel):
    title: str
    creations: List[CommunityCreationItem]


class CountdownTimerConfigResponse(BaseModel):
    title: str
    default_minutes: int
    default_seconds: int
    min_seconds: int
    max_seconds: int


class EmojiRainConfigResponse(BaseModel):
    enabled: bool
    emojis: List[str]
    drop_count: int
    min_duration_ms: int
    max_duration_ms: int
    min_delay_ms: int
    max_delay_ms: int
    min_size_px: int
    max_size_px: int
    opacity: float
    z_index: int
    respect_reduced_motion: bool
    target: str


class ActiveTabShimmerConfigResponse(BaseModel):
    enabled: bool
    gradient_colors: List[str]
    animation_duration_ms: int
    angle_deg: int
    shimmer_width_percent: int
    opacity: float
    respect_reduced_motion: bool
    target: str


class DeployCheckmarkConfigResponse(BaseModel):
    enabled: bool
    size_px: int
    stroke_color: str
    fill_opacity: float
    circle_stroke_width: float
    check_stroke_width: float
    circle_animation_duration_ms: int
    draw_animation_duration_ms: int
    draw_animation_delay_ms: int
    easing: str
    respect_reduced_motion: bool
    animate_only_on_transition: bool
    target: str


class TypingTestConfigResponse(BaseModel):
    title: str
    sentences: List[str]
    time_limit_seconds: int
    words_per_minute_label: str


class TypingTestCalculateRequest(BaseModel):
    original: str
    typed: str
    elapsed_seconds: float


class TypingTestCalculateResponse(BaseModel):
    wpm: float
    accuracy: float
    correct_chars: int
    total_chars: int
    elapsed_seconds: float


class ProgrammingJokeResponse(BaseModel):
    joke: str
    category: str


class AgentFunFactResponse(BaseModel):
    fact: str
    category: str


class PaletteColor(BaseModel):
    hex: str
    rgb: str
    hsl: str


class PaletteGenerateResponse(BaseModel):
    colors: List[PaletteColor]
    harmony: str
    seed_hue: int


class PaletteConfigResponse(BaseModel):
    title: str
    description: str
    harmony_strategies: List[str]
    colors_per_palette: int


class PixelArtConfigResponse(BaseModel):
    title: str
    grid_size: int
    default_color: str
    pixel_size_px: int
    grid_line_color: str
    grid_line_width_px: int
    palette_colors: List[str]
    show_gridlines: bool
    background_color: str


PROGRAMMING_JOKES = [
    {"joke": "Why do programmers prefer dark mode? Because light attracts bugs.", "category": "general"},
    {"joke": "There are only 10 types of people in the world: those who understand binary and those who don't.", "category": "general"},
    {"joke": "A SQL query walks into a bar, walks up to two tables, and asks: Can I join you?", "category": "databases"},
    {"joke": "Why do Java developers wear glasses? Because they can't C#.", "category": "languages"},
    {"joke": "How many programmers does it take to change a light bulb? None, that's a hardware problem.", "category": "general"},
    {"joke": "The best thing about a Boolean is that even if you're wrong, you're only off by a bit.", "category": "general"},
    {"joke": "A programmer's wife tells him: Go to the store and buy a gallon of milk. If they have eggs, get a dozen. He comes back with 12 gallons of milk.", "category": "general"},
    {"joke": "Why was the JavaScript developer sad? Because he didn't Node how to Express himself.", "category": "javascript"},
    {"joke": "What's a programmer's favorite hangout place? Foo Bar.", "category": "general"},
    {"joke": "To understand what recursion is, you must first understand recursion.", "category": "general"},
    {"joke": "There are two hard things in computer science: cache invalidation, naming things, and off-by-one errors.", "category": "general"},
    {"joke": "It works on my machine. Then we'll ship your machine.", "category": "devops"},
]


ASCII_BLOCK_LETTERS = {
    'A': [' ### ', '#   #', '#####', '#   #', '#   #'],
    'B': ['#### ', '#   #', '#### ', '#   #', '#### '],
    'C': [' ####', '#    ', '#    ', '#    ', ' ####'],
    'D': ['#### ', '#   #', '#   #', '#   #', '#### '],
    'E': ['#####', '#    ', '###  ', '#    ', '#####'],
    'F': ['#####', '#    ', '###  ', '#    ', '#    '],
    'G': [' ####', '#    ', '# ###', '#   #', ' ### '],
    'H': ['#   #', '#   #', '#####', '#   #', '#   #'],
    'I': ['#####', '  #  ', '  #  ', '  #  ', '#####'],
    'J': ['#####', '    #', '    #', '#   #', ' ### '],
    'K': ['#   #', '#  # ', '###  ', '#  # ', '#   #'],
    'L': ['#    ', '#    ', '#    ', '#    ', '#####'],
    'M': ['#   #', '## ##', '# # #', '#   #', '#   #'],
    'N': ['#   #', '##  #', '# # #', '#  ##', '#   #'],
    'O': [' ### ', '#   #', '#   #', '#   #', ' ### '],
    'P': ['#### ', '#   #', '#### ', '#    ', '#    '],
    'Q': [' ### ', '#   #', '# # #', '#  # ', ' ## #'],
    'R': ['#### ', '#   #', '#### ', '#  # ', '#   #'],
    'S': [' ####', '#    ', ' ### ', '    #', '#### '],
    'T': ['#####', '  #  ', '  #  ', '  #  ', '  #  '],
    'U': ['#   #', '#   #', '#   #', '#   #', ' ### '],
    'V': ['#   #', '#   #', '#   #', ' # # ', '  #  '],
    'W': ['#   #', '#   #', '# # #', '## ##', '#   #'],
    'X': ['#   #', ' # # ', '  #  ', ' # # ', '#   #'],
    'Y': ['#   #', ' # # ', '  #  ', '  #  ', '  #  '],
    'Z': ['#####', '   # ', '  #  ', ' #   ', '#####'],
    '0': [' ### ', '#   #', '#   #', '#   #', ' ### '],
    '1': ['  #  ', ' ##  ', '  #  ', '  #  ', '#####'],
    '2': [' ### ', '#   #', '  ## ', ' #   ', '#####'],
    '3': [' ### ', '#   #', '  ## ', '#   #', ' ### '],
    '4': ['#   #', '#   #', '#####', '    #', '    #'],
    '5': ['#####', '#    ', '#### ', '    #', '#### '],
    '6': [' ### ', '#    ', '#### ', '#   #', ' ### '],
    '7': ['#####', '    #', '   # ', '  #  ', '  #  '],
    '8': [' ### ', '#   #', ' ### ', '#   #', ' ### '],
    '9': [' ### ', '#   #', ' ####', '    #', ' ### '],
    ' ': ['     ', '     ', '     ', '     ', '     '],
    '!': ['  #  ', '  #  ', '  #  ', '     ', '  #  '],
    '?': [' ### ', '#   #', '  ## ', '     ', '  #  '],
    '.': ['     ', '     ', '     ', '     ', '  #  '],
    '-': ['     ', '     ', '#####', '     ', '     '],
}

BLANK_CHAR = ['     ', '     ', '     ', '     ', '     ']


def generate_block_art(text: str, block_char: str, empty_char: str) -> str:
    """Generate block-letter ASCII art from text."""
    text = text.upper()
    # Strip control characters
    text = text.replace('\n', '').replace('\r', '').replace('\t', '')
    # Truncate to 20 characters
    text = text[:20]

    patterns = [ASCII_BLOCK_LETTERS.get(ch, BLANK_CHAR) for ch in text]

    if not patterns:
        return '\n'.join([''] * 5)

    rows = []
    for row_idx in range(5):
        row = ' '.join(p[row_idx] for p in patterns)
        row = row.replace('#', block_char).replace(' ', empty_char)
        rows.append(row)

    return '\n'.join(rows)


def hsl_to_rgb(h: int, s: int, l: int) -> tuple:
    """Convert HSL values to RGB. h: 0-359, s: 0-100, l: 0-100."""
    s_norm = s / 100.0
    l_norm = l / 100.0
    c = (1 - abs(2 * l_norm - 1)) * s_norm
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = l_norm - c / 2.0
    if h < 60:
        r1, g1, b1 = c, x, 0
    elif h < 120:
        r1, g1, b1 = x, c, 0
    elif h < 180:
        r1, g1, b1 = 0, c, x
    elif h < 240:
        r1, g1, b1 = 0, x, c
    elif h < 300:
        r1, g1, b1 = x, 0, c
    else:
        r1, g1, b1 = c, 0, x
    return (round((r1 + m) * 255), round((g1 + m) * 255), round((b1 + m) * 255))


def generate_harmonious_palette() -> dict:
    """Generate a random palette of 5 harmonious colors."""
    seed_hue = random.randint(0, 359)
    harmony = random.choice(['analogous', 'triadic', 'split-complementary', 'tetradic-plus', 'monochromatic'])

    if harmony == 'analogous':
        hues = [(seed_hue + i * 30) % 360 for i in range(5)]
    elif harmony == 'triadic':
        hues = [(seed_hue + offset) % 360 for offset in [0, 120, 240, 30, 150]]
    elif harmony == 'split-complementary':
        hues = [(seed_hue + offset) % 360 for offset in [0, 150, 210, 30, 180]]
    elif harmony == 'tetradic-plus':
        hues = [(seed_hue + offset) % 360 for offset in [0, 90, 180, 270, 45]]
    else:  # monochromatic
        hues = [seed_hue] * 5

    colors = []
    if harmony == 'monochromatic':
        sl_pairs = [(70, 45), (60, 55), (80, 50), (55, 60), (75, 40)]
        for i, h in enumerate(hues):
            s, l = sl_pairs[i]
            r, g, b = hsl_to_rgb(h, s, l)
            hex_val = f'#{r:02x}{g:02x}{b:02x}'
            colors.append({'hex': hex_val, 'rgb': f'rgb({r}, {g}, {b})', 'hsl': f'hsl({h}, {s}%, {l}%)'})
    else:
        for h in hues:
            s = random.randint(55, 85)
            l = random.randint(40, 65)
            r, g, b = hsl_to_rgb(h, s, l)
            hex_val = f'#{r:02x}{g:02x}{b:02x}'
            colors.append({'hex': hex_val, 'rgb': f'rgb({r}, {g}, {b})', 'hsl': f'hsl({h}, {s}%, {l}%)'})

    return {'colors': colors, 'harmony': harmony, 'seed_hue': seed_hue}


# ── Utility endpoints ──────────────────────────────────────────────

@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/version")
def version():
    return {"version": "0.4.0", "deployed_by": "agentic-sdlc"}


@router.get("/typewriter-config", response_model=TypewriterConfigResponse)
def get_typewriter_config():
    """Return configuration for the homepage typewriter animation."""
    return {
        "enabled": True,
        "lines": [
            {"text": "Describe a change.", "css_class": ""},
            {"text": "Watch AI build it.", "css_class": "accent"},
        ],
        "speed_ms": 80,
        "start_delay_ms": 300,
    }


@router.get("/back-to-top-config", response_model=BackToTopConfigResponse)
def get_back_to_top_config():
    """Return configuration for the back-to-top button UI component."""
    return {
        "enabled": True,
        "scroll_threshold_px": 400,
        "position_right_px": 32,
        "position_bottom_px": 32,
        "size_px": 44,
        "bg_color": "#6366f1",
        "hover_bg_color": "#4f46e5",
        "icon_color": "#ffffff",
        "border_radius": "50%",
        "transition_ms": 200,
        "scroll_behavior": "smooth",
        "scroll_duration_ms": 600,
        "scroll_easing": "cubic-bezier(0.25, 0.1, 0.25, 1)",
        "respect_reduced_motion": True,
    }


@router.get("/parallax-config", response_model=ParallaxConfigResponse)
def get_parallax_config():
    """Return configuration for the hero section parallax scroll effect."""
    return {
        "enabled": True,
        "speed_factor": 0.3,
        "max_offset_px": 120,
        "direction": "up",
        "easing": "ease-out",
    }


@router.get("/sparkle-config", response_model=SparkleConfigResponse)
def get_sparkle_config():
    """Return configuration for the sparkle animation on the shipped count."""
    return {
        "enabled": True,
        "particle_count": 6,
        "duration_ms": 1200,
        "spread_px": 18,
        "colors": ["#fbbf24", "#f59e0b", "#d97706", "#ffffff"],
        "repeat_interval_ms": 4000,
        "size_px": 6,
        "target": "shipped",
    }


@router.get("/gradient-border-config", response_model=GradientBorderConfigResponse)
def get_gradient_border_config():
    """Return configuration for the gradient border animation on the suggestion input box."""
    return {
        "enabled": True,
        "colors": ["#6366f1", "#8b5cf6", "#ec4899", "#6366f1"],
        "angle_deg": 135,
        "animation_duration_ms": 6000,
        "border_width_px": 2,
        "border_radius": "0.5rem",
        "target": "suggest-input",
    }


@router.get("/tictactoe-config", response_model=TicTacToeConfigResponse)
def get_tictactoe_config():
    """Return configuration for the tic-tac-toe game."""
    return {
        "board_size": 3,
        "player_symbols": ["X", "O"],
        "player_colors": ["#6366f1", "#ec4899"],
        "winning_length": 3,
        "empty_cell": "",
        "title": "Tic-Tac-Toe",
    }


@router.get("/suggestions-count", response_model=SuggestionsCountResponse)
def get_suggestions_count(session: Session = Depends(get_session)):
    """Return the total number of suggestions processed."""
    count = session.exec(
        select(func.count(Run.id)).where(Run.workflow == SDLC_WORKFLOW)
    ).one()
    return {"total_suggestions": count, "poll_interval_ms": 10000}


@router.get("/queue-count", response_model=QueueCountResponse)
def get_queue_count(session: Session = Depends(get_session)):
    """Return the number of runs currently in the queue."""
    count = session.exec(
        select(func.count(Run.id)).where(Run.status.in_(["pending", "claimed"]))
    ).one()
    return {"queued_runs": count, "poll_interval_ms": 5000}


@router.get("/markdown-preview-config", response_model=MarkdownPreviewConfigResponse)
def get_markdown_preview_config():
    """Return configuration for the markdown preview tool."""
    return {
        "title": "Markdown Preview",
        "default_markdown": "# Hello\n\nStart typing markdown here...\n\n- Supports **bold** and *italic*\n- Lists and headings\n- Code blocks and more",
        "editor_placeholder": "Type your markdown here...",
        "debounce_ms": 200,
    }


@router.get("/color-picker-config", response_model=ColorPickerConfigResponse)
def get_color_picker_config():
    """Return configuration for the color picker tool."""
    return {
        "title": "Color Picker",
        "default_color": "#6366f1",
        "formats": ["hex", "rgb", "hsl"],
        "show_preview": True,
        "preset_colors": ["#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6", "#8b5cf6", "#ec4899", "#ffffff", "#000000"],
    }


@router.get("/palette-config", response_model=PaletteConfigResponse)
def get_palette_config():
    """Return configuration for the palette generator tool."""
    return {
        "title": "Color Palette Generator",
        "description": "Generate harmonious color palettes with a single click",
        "harmony_strategies": ["analogous", "triadic", "split-complementary", "tetradic-plus", "monochromatic"],
        "colors_per_palette": 5,
    }


@router.get("/palette-generate", response_model=PaletteGenerateResponse)
def generate_palette():
    """Generate a random palette of 5 harmonious colors."""
    return generate_harmonious_palette()


@router.get("/pixel-art-config", response_model=PixelArtConfigResponse)
def get_pixel_art_config():
    """Return configuration for the pixel art canvas."""
    return {
        "title": "Pixel Art Canvas",
        "grid_size": 16,
        "default_color": "#ffffff",
        "pixel_size_px": 24,
        "grid_line_color": "#e5e7eb",
        "grid_line_width_px": 1,
        "palette_colors": ["#000000", "#ffffff", "#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6", "#8b5cf6", "#ec4899", "#6b7280", "#92400e", "#065f46", "#1e3a5f", "#fbbf24", "#7c3aed", "#db2777"],
        "show_gridlines": True,
        "background_color": "#ffffff",
    }


@router.get("/programming-joke", response_model=ProgrammingJokeResponse)
def get_programming_joke():
    """Return a random programming joke."""
    return random.choice(PROGRAMMING_JOKES)


AI_AGENT_FUN_FACTS = [
    {"fact": "These 25 agents coordinate through a multi-stage DAG workflow.", "category": "architecture"},
    {"fact": "Each AI agent specializes in one task, like microservices for thinking.", "category": "architecture"},
    {"fact": "The safety reviewer agent has vetoed more suggestions than any human.", "category": "safety"},
    {"fact": "AI agents don't need coffee breaks, but they do need token budgets.", "category": "humor"},
    {"fact": "The code review agent checks for OWASP Top 10 on every deploy.", "category": "security"},
    {"fact": "The planning agent writes tests before code — true TDD.", "category": "process"},
    {"fact": "On average, an AI agent completes its task in under 60 seconds.", "category": "performance"},
    {"fact": "The deploy agent only ships code that passes every prior stage.", "category": "safety"},
    {"fact": "These agents have processed thousands of community suggestions.", "category": "community"},
    {"fact": "All 25 agents run in parallel stages to maximize throughput.", "category": "performance"},
]


@router.get("/agent-fun-fact", response_model=AgentFunFactResponse)
def get_agent_fun_fact():
    """Return a random fun fact about the AI agents."""
    return random.choice(AI_AGENT_FUN_FACTS)


@router.get("/bounce-button-config", response_model=BounceButtonConfigResponse)
def get_bounce_button_config():
    """Return configuration for the gentle bounce animation on the submit button when it becomes enabled."""
    return {
        "enabled": True,
        "scale_start": 1.0,
        "scale_peak": 1.07,
        "duration_ms": 600,
        "easing": "cubic-bezier(0.34, 1.56, 0.64, 1)",
        "iteration_count": 2,
        "delay_ms": 100,
        "debounce_ms": 300,
        "skip_initial_render": True,
        "respect_reduced_motion": True,
        "target": "submit-button",
    }


@router.get("/suggestion-chip-bounce-config", response_model=SuggestionChipBounceConfigResponse)
def get_suggestion_chip_bounce_config():
    """Return configuration for the gentle bounce animation on suggestion chips when the page first loads."""
    return {
        "enabled": True,
        "translate_y_px": 4.0,
        "duration_ms": 500,
        "easing": "cubic-bezier(0.34, 1.56, 0.64, 1)",
        "stagger_ms": 80,
        "initial_delay_ms": 300,
        "iteration_count": 1,
        "respect_reduced_motion": True,
        "target": "suggestion-chip",
    }


@router.get("/confetti-config", response_model=ConfettiConfigResponse)
def get_confetti_config():
    """Return configuration for the confetti burst animation on run card deploy transitions."""
    return {
        "enabled": True,
        "particle_count": 40,
        "duration_ms": 1500,
        "spread_px": 60,
        "colors": ["#34d399", "#6366f1", "#fbbf24", "#ec4899", "#3b82f6"],
        "gravity": 0.8,
        "drift": 0.5,
        "size_range": [4, 8],
        "shapes": ["circle", "square"],
        "trigger": "status-change",
        "trigger_from": "running",
        "trigger_to": "deployed",
        "respect_reduced_motion": True,
        "target": "run-card",
        "max_concurrent": 3,
    }


@router.get("/pipeline-glow-config", response_model=PipelineGlowConfigResponse)
def get_pipeline_glow_config():
    """Return configuration for the progressive glow effect on completed pipeline stage circles."""
    return {
        "enabled": True,
        "glow_color_rgb": "102, 187, 106",
        "min_blur_px": 4,
        "max_blur_px": 18,
        "min_spread_px": 1,
        "max_spread_px": 6,
        "min_opacity": 0.25,
        "max_opacity": 0.7,
        "animation_duration_ms": 2000,
        "total_stages": 7,
        "respect_reduced_motion": True,
        "target": "pipeline-stage",
    }


@router.get("/ascii-art-config", response_model=AsciiArtConfigResponse)
def get_ascii_art_config():
    """Return configuration for the ASCII art generator tool."""
    return {
        "enabled": True,
        "title": "ASCII Art Generator",
        "default_text": "HELLO",
        "max_length": 20,
        "block_char": "#",
        "empty_char": " ",
        "supported_characters": "A-Z 0-9 ! ? . -",
        "letter_height": 5,
    }


@router.get("/countdown-timer-config", response_model=CountdownTimerConfigResponse)
def get_countdown_timer_config():
    """Return configuration for the countdown timer widget."""
    return {
        "title": "Countdown Timer",
        "default_minutes": 5,
        "default_seconds": 0,
        "min_seconds": 1,
        "max_seconds": 5999,
    }


@router.get("/emoji-rain-config", response_model=EmojiRainConfigResponse)
def get_emoji_rain_config():
    """Return configuration for the emoji rain animation behind the hero section."""
    return {
        "enabled": True,
        "emojis": ["🚀", "✨", "💻", "🎉", "⚡", "🔥", "🌈", "💡", "🎯", "🛠️"],
        "drop_count": 25,
        "min_duration_ms": 3000,
        "max_duration_ms": 7000,
        "min_delay_ms": 0,
        "max_delay_ms": 5000,
        "min_size_px": 16,
        "max_size_px": 32,
        "opacity": 0.3,
        "z_index": -1,
        "respect_reduced_motion": True,
        "target": "hero-section",
    }


@router.get("/active-tab-shimmer-config", response_model=ActiveTabShimmerConfigResponse)
def get_active_tab_shimmer_config():
    """Return configuration for the gradient shimmer effect on the active filter tab."""
    return {
        "enabled": True,
        "gradient_colors": ["rgba(99,102,241,0)", "rgba(99,102,241,0.4)", "rgba(139,92,246,0.5)", "rgba(99,102,241,0.4)", "rgba(99,102,241,0)"],
        "animation_duration_ms": 2000,
        "angle_deg": 120,
        "shimmer_width_percent": 30,
        "opacity": 0.6,
        "respect_reduced_motion": True,
        "target": "active-filter-tab",
    }


@router.get("/deploy-checkmark-config", response_model=DeployCheckmarkConfigResponse)
def get_deploy_checkmark_config():
    """Return configuration for the animated checkmark icon displayed on deployed run cards."""
    return {
        "enabled": True,
        "size_px": 20,
        "stroke_color": "#34d399",
        "fill_opacity": 0.1,
        "circle_stroke_width": 2.0,
        "check_stroke_width": 2.5,
        "circle_animation_duration_ms": 400,
        "draw_animation_duration_ms": 300,
        "draw_animation_delay_ms": 200,
        "easing": "ease-out",
        "respect_reduced_motion": True,
        "animate_only_on_transition": True,
        "target": "deployed-run-card",
    }


@router.get("/typing-test-config", response_model=TypingTestConfigResponse)
def get_typing_test_config():
    """Return configuration for the typing speed test."""
    return {
        "title": "Typing Speed Test",
        "sentences": [
            "The quick brown fox jumps over the lazy dog.",
            "Pack my box with five dozen liquor jugs.",
            "How vexingly quick daft zebras jump.",
            "The five boxing wizards jump quickly.",
            "Sphinx of black quartz, judge my vow.",
        ],
        "time_limit_seconds": 60,
        "words_per_minute_label": "WPM",
    }


@router.post("/typing-test-calculate", response_model=TypingTestCalculateResponse)
def calculate_typing_speed(body: TypingTestCalculateRequest):
    """Calculate typing speed (WPM) and accuracy from original and typed text."""
    if body.elapsed_seconds <= 0:
        raise HTTPException(status_code=400, detail="Elapsed time must be positive")

    correct_chars = sum(1 for a, b in zip(body.original, body.typed) if a == b)
    total_chars = len(body.original)
    accuracy = round((correct_chars / total_chars) * 100, 1) if total_chars > 0 else 0.0
    word_count = len(body.typed.strip().split()) if body.typed.strip() else 0
    wpm = round((word_count / body.elapsed_seconds) * 60, 1)

    return {
        "wpm": wpm,
        "accuracy": accuracy,
        "correct_chars": correct_chars,
        "total_chars": total_chars,
        "elapsed_seconds": body.elapsed_seconds,
    }


@router.post("/ascii-art-generate", response_model=AsciiArtResponse)
def generate_ascii_art_endpoint(body: AsciiArtRequest):
    """Generate block-letter ASCII art from input text."""
    stripped = body.text.strip()
    if not stripped:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    art = generate_block_art(stripped, "#", " ")
    width = len(art.split('\n')[0]) if art else 0
    original = stripped.upper()[:20]

    return {
        "art": art,
        "original_text": original,
        "width": width,
        "height": 5,
    }


@router.get("/community-creations-config", response_model=CommunityCreationsConfigResponse)
def get_community_creations_config():
    """Return configuration for the community creations section on the homepage."""
    return {
        "title": "These pages were built entirely by AI from user suggestions",
        "creations": [
            {"name": "Tic-Tac-Toe", "description": "A classic two-player game built with React", "path": "/games/tictactoe"},
            {"name": "Color Picker", "description": "Pick colors and convert between hex, RGB, and HSL formats", "path": "/tools/colors"},
            {"name": "ASCII Art Generator", "description": "Turn text into block-letter ASCII art", "path": "/tools/ascii"},
            {"name": "Markdown Preview", "description": "Live preview editor for Markdown syntax", "path": "/tools/markdown"},
            {"name": "Countdown Timer", "description": "A simple countdown timer with start, stop, and reset controls", "path": "/tools/timer"},
            {"name": "Typing Speed Test", "description": "Test your typing speed and accuracy", "path": "/games/typing-test"},
            {"name": "Palette Generator", "description": "Generate harmonious color palettes with one click", "path": "/tools/palette"},
            {"name": "Pixel Art Canvas", "description": "Draw pixel art on an interactive 16x16 grid", "path": "/games/pixel-art"},
        ],
    }


# ── Suggestion endpoint ───────────────────────────────────────────

@router.post("/suggest")
def suggest(body: SuggestRequest, session: Session = Depends(get_session)):
    """Submit a feature suggestion. Creates a pending run for the worker."""
    if not body.suggestion.strip():
        raise HTTPException(status_code=400, detail="Suggestion cannot be empty")
    run = Run(
        id=str(uuid.uuid4()),
        workflow=SDLC_WORKFLOW,
        inputs=json.dumps({"task_description": body.suggestion}),
    )
    session.add(run)
    session.commit()
    return {
        "status": "submitted",
        "run_id": run.id,
        "message": "Your suggestion has been submitted. A worker will pick it up shortly.",
    }


# ── Worker endpoints ──────────────────────────────────────────────

@router.post("/runs/{run_id}/claim")
def claim_run(run_id: str, body: ClaimRequest, session: Session = Depends(get_session)):
    """Worker claims a pending run."""
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status != "pending":
        raise HTTPException(status_code=409, detail=f"Run is already {run.status}")
    run.status = "claimed"
    run.worker_id = body.worker_id
    run.started_at = datetime.now(UTC)
    session.add(run)
    session.commit()
    return {"status": "claimed", "run_id": run.id}


@router.put("/runs/{run_id}/status")
def update_run_status(
    run_id: str, body: CompleteRequest, session: Session = Depends(get_session)
):
    """Worker updates run status (running, completed, failed)."""
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    run.status = body.status
    if body.result is not None:
        run.result = json.dumps(body.result)
    if body.error is not None:
        run.error = body.error
    if body.status in ("completed", "failed"):
        run.completed_at = datetime.now(UTC)
    session.add(run)
    session.commit()
    return {"status": run.status, "run_id": run.id}


# ── Run CRUD ──────────────────────────────────────────────────────

@router.post("/runs", response_model=CreateRunResponse)
def create_run(body: CreateRunRequest, session: Session = Depends(get_session)):
    run = Run(
        id=str(uuid.uuid4()),
        workflow=body.workflow,
        inputs=json.dumps(body.inputs),
    )
    session.add(run)
    session.commit()
    return CreateRunResponse(id=run.id, status=run.status)


@router.get("/runs")
def list_runs(
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    query = select(Run).order_by(Run.created_at.desc()).offset(offset).limit(limit)
    if status:
        query = query.where(Run.status == status)
    runs = session.exec(query).all()
    run_list = []
    for r in runs:
        result = r.get_result()
        total_tokens = extract_total_tokens(result)
        run_list.append({
            "id": r.id,
            "workflow": r.workflow,
            "status": r.status,
            "inputs": r.get_inputs(),
            "created_at": r.created_at.isoformat(),
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "error": r.error,
            "has_result": r.result is not None,
            "duration_seconds": calculate_duration(r.started_at, r.completed_at),
            "total_tokens": total_tokens,
            "workflow_output": extract_workflow_output(result),
            "cost_dollars": calculate_cost_dollars(total_tokens),
        })
    return {"runs": run_list, "total": len(runs)}


@router.get("/runs/{run_id}")
def get_run(run_id: str, session: Session = Depends(get_session)):
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    result = run.get_result()
    return {
        "id": run.id,
        "workflow": run.workflow,
        "status": run.status,
        "inputs": run.get_inputs(),
        "result": result,
        "error": run.error,
        "worker_id": run.worker_id,
        "created_at": run.created_at.isoformat(),
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "cost_dollars": calculate_cost_dollars(extract_total_tokens(result)),
    }


@router.get("/runs/{run_id}/events")
def get_run_events(
    run_id: str,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    query = (
        select(RunEvent)
        .where(RunEvent.run_id == run_id)
        .order_by(RunEvent.created_at)
        .offset(offset)
        .limit(limit)
    )
    events = session.exec(query).all()
    return {
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "data": json.loads(e.data) if e.data else {},
                "created_at": e.created_at.isoformat(),
            }
            for e in events
        ],
        "total": len(events),
    }
