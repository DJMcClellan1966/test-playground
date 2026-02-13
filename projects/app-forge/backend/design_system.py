"""
App Forge Design System
=======================
AI-free design intelligence that selects optimal visual styles
based on app category, user intent, and proven UI/UX patterns.

Key insights from building hundreds of apps:
1. Color psychology affects user behavior (blue=trust, green=success)
2. Layout density varies by task type (games=focused, CRUD=spacious)
3. Typography affects reading speed and comprehension
4. Micro-interactions improve perceived quality

Categories:
- productivity: Clean, minimal, professional blues/grays
- creative: Vibrant, expressive, artistic palettes
- game: High contrast, energetic, centered focus
- finance: Trust-inspiring, conservative blues/greens
- social: Friendly, warm, rounded elements
- health: Calm, reassuring, soft greens/blues
- education: Clear, structured, focused
- entertainment: Fun, engaging, bold
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import re
from enum import Enum


class AppCategory(Enum):
    """High-level app categories with distinct design needs."""
    PRODUCTIVITY = "productivity"  # Task lists, notes, trackers
    CREATIVE = "creative"          # Drawing, music, design tools
    GAME = "game"                  # Games, puzzles, entertainment
    FINANCE = "finance"            # Budget, expense, invoice
    SOCIAL = "social"              # Chat, messaging, collaboration
    HEALTH = "health"              # Fitness, wellness, medical
    EDUCATION = "education"        # Learning, quiz, flashcards
    ENTERTAINMENT = "entertainment"  # Media, streaming, fun
    UTILITY = "utility"            # Calculators, converters, tools
    ECOMMERCE = "ecommerce"        # Shopping, inventory, products
    DATA = "data"                  # Analytics, dashboards, reports


class ThemeVariant(Enum):
    """Theme variants that modify the base category theme."""
    DEFAULT = "default"   # Use the category's default palette
    LIGHT = "light"       # Bright, airy feel
    DARK = "dark"         # Dark mode
    WARM = "warm"         # Warm, cozy tones
    COOL = "cool"         # Cool, professional tones


@dataclass
class ColorPalette:
    """Color palette with semantic meaning."""
    primary: str       # Main brand/action color
    secondary: str     # Supporting accent
    background: str    # Page background
    surface: str       # Card/container background
    text: str          # Primary text
    text_muted: str    # Secondary text
    border: str        # Borders and dividers
    success: str       # Success states
    warning: str       # Warning states
    error: str         # Error states
    
    def to_css_vars(self) -> str:
        """Generate CSS custom properties."""
        return f"""
:root {{
    --color-primary: {self.primary};
    --color-secondary: {self.secondary};
    --color-bg: {self.background};
    --color-surface: {self.surface};
    --color-text: {self.text};
    --color-text-muted: {self.text_muted};
    --color-border: {self.border};
    --color-success: {self.success};
    --color-warning: {self.warning};
    --color-error: {self.error};
}}"""


@dataclass
class Typography:
    """Typography settings."""
    font_family: str
    font_size_base: str
    font_size_lg: str
    font_size_sm: str
    line_height: str
    heading_weight: str
    body_weight: str


@dataclass
class Spacing:
    """Spacing scale."""
    xs: str = "4px"
    sm: str = "8px"
    md: str = "16px"
    lg: str = "24px"
    xl: str = "32px"
    xxl: str = "48px"


@dataclass
class LayoutStyle:
    """Layout characteristics."""
    max_width: str         # Container max width
    padding: str           # Container padding
    card_radius: str       # Card corner radius
    button_radius: str     # Button corner radius
    shadow: str            # Box shadow style
    density: str           # compact, normal, spacious


@dataclass
class DesignTheme:
    """Complete design theme for an app."""
    name: str
    category: AppCategory
    palette: ColorPalette
    typography: Typography
    spacing: Spacing
    layout: LayoutStyle
    
    # Special features
    dark_mode: bool = False
    animations: bool = True
    glassmorphism: bool = False
    gradients: bool = False
    
    def generate_css(self) -> str:
        """Generate complete CSS for this theme."""
        css = [self.palette.to_css_vars()]
        
        css.append(f"""
* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
    font-family: {self.typography.font_family};
    font-size: {self.typography.font_size_base};
    line-height: {self.typography.line_height};
    font-weight: {self.typography.body_weight};
    background: var(--color-bg);
    color: var(--color-text);
    min-height: 100vh;
}}

.container {{
    max-width: {self.layout.max_width};
    margin: 0 auto;
    padding: {self.layout.padding};
}}

.card {{
    background: var(--color-surface);
    border-radius: {self.layout.card_radius};
    padding: {self.spacing.lg};
    {"box-shadow: " + self.layout.shadow + ";" if self.layout.shadow else "border: 1px solid var(--color-border);"}
    margin-bottom: {self.spacing.md};
}}

.navbar {{
    background: var(--color-primary);
    color: #fff;
    padding: {self.spacing.md} {self.spacing.lg};
    text-align: center;
    {"position: sticky; top: 0; z-index: 100;" if self.category != AppCategory.GAME else ""}
}}

.navbar h1 {{
    font-size: {self.typography.font_size_lg};
    font-weight: {self.typography.heading_weight};
}}

h1, h2, h3, h4, h5, h6 {{
    font-weight: {self.typography.heading_weight};
    color: var(--color-text);
    margin-bottom: {self.spacing.sm};
}}

button {{
    padding: {self.spacing.sm} {self.spacing.md};
    border: none;
    border-radius: {self.layout.button_radius};
    cursor: pointer;
    font-size: {self.typography.font_size_base};
    font-weight: 600;
    font-family: inherit;
    {"transition: all 0.2s ease;" if self.animations else ""}
}}

.btn-primary {{
    background: var(--color-primary);
    color: #fff;
}}

.btn-primary:hover {{
    filter: brightness(1.1);
    {"transform: translateY(-1px);" if self.animations else ""}
}}

.btn-secondary {{
    background: var(--color-surface);
    color: var(--color-text);
    border: 1px solid var(--color-border);
}}

.btn-secondary:hover {{
    background: var(--color-bg);
}}

input, select, textarea {{
    padding: {self.spacing.sm} {self.spacing.md};
    border: 1px solid var(--color-border);
    border-radius: {self.layout.button_radius};
    font-size: {self.typography.font_size_base};
    font-family: inherit;
    width: 100%;
    margin-bottom: {self.spacing.sm};
    background: var(--color-surface);
    color: var(--color-text);
}}

input:focus, select:focus, textarea:focus {{
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(var(--color-primary-rgb, 0,0,0), 0.15);
}}

.text-muted {{ color: var(--color-text-muted); }}
.text-success {{ color: var(--color-success); }}
.text-warning {{ color: var(--color-warning); }}
.text-error {{ color: var(--color-error); }}

.badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: {self.typography.font_size_sm};
    font-weight: 600;
}}

.badge-primary {{ background: var(--color-primary); color: #fff; }}
.badge-success {{ background: var(--color-success); color: #fff; }}
.badge-warning {{ background: var(--color-warning); color: #000; }}
.badge-error {{ background: var(--color-error); color: #fff; }}
""")
        
        # Add dark mode support
        if self.dark_mode:
            css.append("""
@media (prefers-color-scheme: dark) {
    :root {
        --color-bg: #1a1a2e;
        --color-surface: #16213e;
        --color-text: #eaeaea;
        --color-text-muted: #a0a0a0;
        --color-border: #2a2a4e;
    }
}
""")
        
        # Add glassmorphism
        if self.glassmorphism:
            css.append("""
.card {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
}
""")
        
        return '\n'.join(css)


# =============================================================================
# PREDEFINED THEMES BY CATEGORY
# =============================================================================

THEMES: Dict[AppCategory, DesignTheme] = {}

# Productivity Theme - Clean, professional, trustworthy
THEMES[AppCategory.PRODUCTIVITY] = DesignTheme(
    name="Modern Productivity",
    category=AppCategory.PRODUCTIVITY,
    palette=ColorPalette(
        primary="#2563eb",      # Blue - trust, focus
        secondary="#3b82f6",
        background="#f8fafc",
        surface="#ffffff",
        text="#1e293b",
        text_muted="#64748b",
        border="#e2e8f0",
        success="#22c55e",
        warning="#f59e0b",
        error="#ef4444",
    ),
    typography=Typography(
        font_family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        font_size_base="15px",
        font_size_lg="20px",
        font_size_sm="13px",
        line_height="1.6",
        heading_weight="600",
        body_weight="400",
    ),
    spacing=Spacing(),
    layout=LayoutStyle(
        max_width="800px",
        padding="20px",
        card_radius="12px",
        button_radius="8px",
        shadow="0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)",
        density="normal",
    ),
)

# Game Theme - High contrast, centered, focused
THEMES[AppCategory.GAME] = DesignTheme(
    name="Game Focus",
    category=AppCategory.GAME,
    palette=ColorPalette(
        primary="#8b5cf6",      # Purple - energetic, playful
        secondary="#a78bfa",
        background="#0f0f1a",
        surface="#1a1a2e",
        text="#ffffff",
        text_muted="#a0a0b0",
        border="#2a2a4e",
        success="#22c55e",
        warning="#fbbf24",
        error="#f87171",
    ),
    typography=Typography(
        font_family='"Inter", -apple-system, BlinkMacSystemFont, sans-serif',
        font_size_base="16px",
        font_size_lg="24px",
        font_size_sm="14px",
        line_height="1.4",
        heading_weight="700",
        body_weight="400",
    ),
    spacing=Spacing(),
    layout=LayoutStyle(
        max_width="600px",
        padding="16px",
        card_radius="16px",
        button_radius="12px",
        shadow="0 4px 20px rgba(0,0,0,0.3)",
        density="compact",
    ),
    dark_mode=True,
    animations=True,
)

# Finance Theme - Trust, security, conservative
THEMES[AppCategory.FINANCE] = DesignTheme(
    name="Finance Professional",
    category=AppCategory.FINANCE,
    palette=ColorPalette(
        primary="#059669",      # Green - money, growth
        secondary="#10b981",
        background="#f0fdf4",
        surface="#ffffff",
        text="#1e3a2f",
        text_muted="#6b7c74",
        border="#d1e7dd",
        success="#22c55e",
        warning="#f59e0b",
        error="#dc2626",
    ),
    typography=Typography(
        font_family='"Inter", -apple-system, BlinkMacSystemFont, sans-serif',
        font_size_base="14px",
        font_size_lg="18px",
        font_size_sm="12px",
        line_height="1.5",
        heading_weight="600",
        body_weight="400",
    ),
    spacing=Spacing(),
    layout=LayoutStyle(
        max_width="900px",
        padding="24px",
        card_radius="8px",
        button_radius="6px",
        shadow="0 1px 2px rgba(0,0,0,0.05)",
        density="normal",
    ),
)

# Creative Theme - Vibrant, expressive
THEMES[AppCategory.CREATIVE] = DesignTheme(
    name="Creative Studio",
    category=AppCategory.CREATIVE,
    palette=ColorPalette(
        primary="#ec4899",      # Pink - creative, artistic
        secondary="#f472b6",
        background="#fdf2f8",
        surface="#ffffff",
        text="#1f1f1f",
        text_muted="#6b6b6b",
        border="#fce7f3",
        success="#22c55e",
        warning="#f59e0b",
        error="#ef4444",
    ),
    typography=Typography(
        font_family='"Poppins", -apple-system, sans-serif',
        font_size_base="15px",
        font_size_lg="22px",
        font_size_sm="13px",
        line_height="1.6",
        heading_weight="700",
        body_weight="400",
    ),
    spacing=Spacing(),
    layout=LayoutStyle(
        max_width="1000px",
        padding="20px",
        card_radius="16px",
        button_radius="24px",  # Pill buttons
        shadow="0 4px 12px rgba(236,72,153,0.15)",
        density="spacious",
    ),
    gradients=True,
)

# Health Theme - Calm, reassuring
THEMES[AppCategory.HEALTH] = DesignTheme(
    name="Wellness",
    category=AppCategory.HEALTH,
    palette=ColorPalette(
        primary="#14b8a6",      # Teal - calm, health
        secondary="#2dd4bf",
        background="#f0fdfa",
        surface="#ffffff",
        text="#134e4a",
        text_muted="#5f9ea0",
        border="#ccfbf1",
        success="#22c55e",
        warning="#f59e0b",
        error="#f87171",
    ),
    typography=Typography(
        font_family='"Nunito", -apple-system, sans-serif',
        font_size_base="16px",
        font_size_lg="22px",
        font_size_sm="14px",
        line_height="1.7",
        heading_weight="600",
        body_weight="400",
    ),
    spacing=Spacing(md="20px", lg="28px"),
    layout=LayoutStyle(
        max_width="700px",
        padding="24px",
        card_radius="20px",
        button_radius="12px",
        shadow="0 2px 8px rgba(20,184,166,0.1)",
        density="spacious",
    ),
)

# Education Theme - Clear, structured
THEMES[AppCategory.EDUCATION] = DesignTheme(
    name="Learning",
    category=AppCategory.EDUCATION,
    palette=ColorPalette(
        primary="#f59e0b",      # Amber - attention, learning
        secondary="#fbbf24",
        background="#fffbeb",
        surface="#ffffff",
        text="#292524",
        text_muted="#78716c",
        border="#fde68a",
        success="#22c55e",
        warning="#f59e0b",
        error="#ef4444",
    ),
    typography=Typography(
        font_family='"Source Sans Pro", -apple-system, sans-serif',
        font_size_base="16px",
        font_size_lg="24px",
        font_size_sm="14px",
        line_height="1.7",
        heading_weight="600",
        body_weight="400",
    ),
    spacing=Spacing(),
    layout=LayoutStyle(
        max_width="800px",
        padding="24px",
        card_radius="12px",
        button_radius="8px",
        shadow="0 2px 4px rgba(245,158,11,0.1)",
        density="normal",
    ),
)

# Social Theme - Friendly, warm
THEMES[AppCategory.SOCIAL] = DesignTheme(
    name="Social Friendly",
    category=AppCategory.SOCIAL,
    palette=ColorPalette(
        primary="#f97316",      # Orange - friendly, warm
        secondary="#fb923c",
        background="#fff7ed",
        surface="#ffffff",
        text="#1c1917",
        text_muted="#78716c",
        border="#fed7aa",
        success="#22c55e",
        warning="#f59e0b",
        error="#ef4444",
    ),
    typography=Typography(
        font_family='"Inter", -apple-system, sans-serif',
        font_size_base="15px",
        font_size_lg="20px",
        font_size_sm="13px",
        line_height="1.5",
        heading_weight="600",
        body_weight="400",
    ),
    spacing=Spacing(),
    layout=LayoutStyle(
        max_width="700px",
        padding="16px",
        card_radius="16px",
        button_radius="20px",
        shadow="0 2px 8px rgba(249,115,22,0.1)",
        density="normal",
    ),
)

# Utility Theme - Minimal, functional
THEMES[AppCategory.UTILITY] = DesignTheme(
    name="Utility",
    category=AppCategory.UTILITY,
    palette=ColorPalette(
        primary="#6366f1",      # Indigo - professional tool
        secondary="#818cf8",
        background="#f5f5f5",
        surface="#ffffff",
        text="#1f2937",
        text_muted="#6b7280",
        border="#e5e7eb",
        success="#22c55e",
        warning="#f59e0b",
        error="#ef4444",
    ),
    typography=Typography(
        font_family='ui-monospace, "SF Mono", monospace',
        font_size_base="14px",
        font_size_lg="18px",
        font_size_sm="12px",
        line_height="1.5",
        heading_weight="600",
        body_weight="400",
    ),
    spacing=Spacing(),
    layout=LayoutStyle(
        max_width="500px",
        padding="20px",
        card_radius="8px",
        button_radius="6px",
        shadow="none",
        density="compact",
    ),
)

# Entertainment Theme - Fun, bold
THEMES[AppCategory.ENTERTAINMENT] = DesignTheme(
    name="Entertainment",
    category=AppCategory.ENTERTAINMENT,
    palette=ColorPalette(
        primary="#e11d48",      # Rose - exciting, fun
        secondary="#fb7185",
        background="#1a1a2e",
        surface="#2d2d44",
        text="#ffffff",
        text_muted="#a1a1aa",
        border="#3f3f5e",
        success="#22c55e",
        warning="#fbbf24",
        error="#f87171",
    ),
    typography=Typography(
        font_family='"Inter", -apple-system, sans-serif',
        font_size_base="16px",
        font_size_lg="28px",
        font_size_sm="14px",
        line_height="1.4",
        heading_weight="800",
        body_weight="400",
    ),
    spacing=Spacing(),
    layout=LayoutStyle(
        max_width="900px",
        padding="20px",
        card_radius="16px",
        button_radius="12px",
        shadow="0 8px 32px rgba(0,0,0,0.3)",
        density="normal",
    ),
    dark_mode=True,
    animations=True,
)

# Data/Dashboard Theme - Information dense
THEMES[AppCategory.DATA] = DesignTheme(
    name="Data Dashboard",
    category=AppCategory.DATA,
    palette=ColorPalette(
        primary="#0ea5e9",      # Sky blue - clarity, information
        secondary="#38bdf8",
        background="#f0f9ff",
        surface="#ffffff",
        text="#0c4a6e",
        text_muted="#64748b",
        border="#bae6fd",
        success="#22c55e",
        warning="#f59e0b",
        error="#ef4444",
    ),
    typography=Typography(
        font_family='"Inter", -apple-system, sans-serif',
        font_size_base="13px",
        font_size_lg="16px",
        font_size_sm="11px",
        line_height="1.4",
        heading_weight="600",
        body_weight="400",
    ),
    spacing=Spacing(sm="6px", md="12px", lg="18px"),
    layout=LayoutStyle(
        max_width="1200px",
        padding="16px",
        card_radius="8px",
        button_radius="6px",
        shadow="0 1px 2px rgba(0,0,0,0.05)",
        density="compact",
    ),
)

# E-commerce Theme
THEMES[AppCategory.ECOMMERCE] = DesignTheme(
    name="Shop",
    category=AppCategory.ECOMMERCE,
    palette=ColorPalette(
        primary="#7c3aed",      # Violet - premium, shopping
        secondary="#8b5cf6",
        background="#faf5ff",
        surface="#ffffff",
        text="#1e1b4b",
        text_muted="#6b7280",
        border="#e9d5ff",
        success="#22c55e",
        warning="#f59e0b",
        error="#ef4444",
    ),
    typography=Typography(
        font_family='"Inter", -apple-system, sans-serif',
        font_size_base="15px",
        font_size_lg="20px",
        font_size_sm="13px",
        line_height="1.5",
        heading_weight="600",
        body_weight="400",
    ),
    spacing=Spacing(),
    layout=LayoutStyle(
        max_width="1100px",
        padding="20px",
        card_radius="12px",
        button_radius="8px",
        shadow="0 2px 8px rgba(124,58,237,0.1)",
        density="normal",
    ),
)


# =============================================================================
# CATEGORY DETECTION
# =============================================================================

CATEGORY_PATTERNS: List[Tuple[AppCategory, List[str]]] = [
    (AppCategory.GAME, [
        r"game|play|puzzle|quiz|trivia|wordle|hangman|tic.?tac.?toe|snake|tetris",
        r"minesweeper|sudoku|memory.?game|matching|cards?|dice|casino|slots",
        r"arcade|score|level|lives|player|opponent|challenge|leaderboard",
    ]),
    (AppCategory.FINANCE, [
        r"budget|expense|money|finance|invoice|payment|banking|account",
        r"transaction|salary|income|tax|bill|loan|mortgage|invest|stock",
        r"crypto|wallet|currency|exchange|profit|loss|portfolio",
    ]),
    (AppCategory.HEALTH, [
        r"health|fitness|workout|exercise|gym|yoga|meditation|wellness",
        r"diet|nutrition|calories?|weight|bmi|sleep|habit|water|steps",
        r"mental|therapy|mood|journal|mindful|breathing|heart.?rate",
    ]),
    (AppCategory.EDUCATION, [
        r"learn|study|education|course|lesson|tutorial|quiz|test|exam",
        r"flashcard|vocabulary|language|math|science|history|grade|school",
        r"student|teacher|classroom|homework|practice|knowledge",
    ]),
    (AppCategory.CREATIVE, [
        r"draw|paint|art|design|photo|image|video|music|audio|creative",
        r"canvas|sketch|color|palette|editor|collage|filter|effect",
        r"compose|beat|instrument|animation|illustration|graphic",
    ]),
    (AppCategory.SOCIAL, [
        r"chat|message|social|friend|profile|share|comment|like|follow",
        r"community|forum|discussion|post|feed|notification|group",
        r"connect|network|dating|match|meet|collaborate",
    ]),
    (AppCategory.ENTERTAINMENT, [
        r"movie|film|tv|show|video|stream|music|playlist|podcast",
        r"entertainment|media|watch|listen|discover|recommend|rate|review",
    ]),
    (AppCategory.ECOMMERCE, [
        r"shop|store|product|cart|checkout|order|inventory|catalog",
        r"e.?commerce|buy|sell|price|discount|shipping|customer|merchant",
    ]),
    (AppCategory.DATA, [
        r"dashboard|analytics|report|chart|graph|metrics|statistics",
        r"data|monitor|track|visuali[sz]e|insight|kpi|performance",
    ]),
    (AppCategory.UTILITY, [
        r"calculator|converter|timer|stopwatch|clock|countdown|alarm",
        r"password|generator|random|qr|barcode|unit|measurement",
        r"tool|utility|helper|validator|formatter|encoder|decoder",
    ]),
    (AppCategory.PRODUCTIVITY, [
        r"todo|task|project|note|reminder|calendar|schedule|planner",
        r"bookmark|organize|manage|list|track|log|record|productivity",
        r"recipe|inventory|collection|library|catalog|crm|contact",
    ]),
]


def detect_category(description: str) -> AppCategory:
    """Detect app category from description using pattern matching.
    
    Returns the most confident category match.
    """
    desc = description.lower()
    scores: Dict[AppCategory, int] = {cat: 0 for cat in AppCategory}
    
    for category, patterns in CATEGORY_PATTERNS:
        for pattern in patterns:
            matches = len(re.findall(pattern, desc))
            scores[category] += matches * 2  # Each match adds 2 points
    
    # Find best match
    best = max(scores.items(), key=lambda x: x[1])
    
    # Default to productivity if no strong match
    if best[1] < 2:
        return AppCategory.PRODUCTIVITY
    
    return best[0]


def get_theme_for_description(description: str, variant: ThemeVariant = ThemeVariant.DEFAULT) -> DesignTheme:
    """Get the optimal design theme for an app description with optional variant."""
    category = detect_category(description)
    theme = THEMES.get(category, THEMES[AppCategory.PRODUCTIVITY])
    
    if variant == ThemeVariant.DEFAULT:
        return theme
    
    return apply_variant(theme, variant)


def apply_variant(theme: DesignTheme, variant: ThemeVariant) -> DesignTheme:
    """Apply a color variant to a theme, preserving the category's primary color."""
    from copy import deepcopy
    
    new_theme = deepcopy(theme)
    p = theme.palette
    
    if variant == ThemeVariant.DARK:
        new_theme.palette = ColorPalette(
            primary=p.primary,
            secondary=p.secondary,
            background="#1a1a2e",
            surface="#2d2d44",
            text="#ffffff",
            text_muted="#a0a0b0",
            border="#3d3d5c",
            success="#22c55e",
            warning="#fbbf24",
            error="#f87171",
        )
        new_theme.dark_mode = True
        new_theme.name = f"{theme.name} (Dark)"
        
    elif variant == ThemeVariant.LIGHT:
        new_theme.palette = ColorPalette(
            primary=p.primary,
            secondary=p.secondary,
            background="#fafafa",
            surface="#ffffff",
            text="#1f2937",
            text_muted="#6b7280",
            border="#e5e7eb",
            success="#10b981",
            warning="#f59e0b",
            error="#ef4444",
        )
        new_theme.dark_mode = False
        new_theme.name = f"{theme.name} (Light)"
        
    elif variant == ThemeVariant.WARM:
        new_theme.palette = ColorPalette(
            primary=p.primary,
            secondary=p.secondary,
            background="#fdf6e3",
            surface="#fff8dc",
            text="#5c4827",
            text_muted="#8b7355",
            border="#e6d5b8",
            success="#059669",
            warning="#d97706",
            error="#dc2626",
        )
        new_theme.dark_mode = False
        new_theme.name = f"{theme.name} (Warm)"
        
    elif variant == ThemeVariant.COOL:
        new_theme.palette = ColorPalette(
            primary=p.primary,
            secondary=p.secondary,
            background="#f0f9ff",
            surface="#ffffff",
            text="#1e3a5f",
            text_muted="#64748b",
            border="#cbd5e1",
            success="#059669",
            warning="#eab308",
            error="#e11d48",
        )
        new_theme.dark_mode = False
        new_theme.name = f"{theme.name} (Cool)"
    
    return new_theme


def get_category_css(description: str, variant: ThemeVariant = ThemeVariant.DEFAULT) -> str:
    """Generate CSS for an app based on its description and optional variant."""
    theme = get_theme_for_description(description, variant)
    return theme.generate_css()


def get_available_variants() -> List[dict]:
    """Return list of available theme variants for UI display."""
    return [
        {"id": "default", "name": "Default", "description": "Category-optimized theme"},
        {"id": "light", "name": "Light", "description": "Bright, airy feel"},
        {"id": "dark", "name": "Dark", "description": "Dark mode for low-light use"},
        {"id": "warm", "name": "Warm", "description": "Cozy, sepia-toned"},
        {"id": "cool", "name": "Cool", "description": "Professional, blue-tinted"},
    ]


# =============================================================================
# CSS HELPER FUNCTIONS
# =============================================================================

def get_base_css(theme: DesignTheme) -> str:
    """Get base CSS that applies to all components."""
    return theme.generate_css()


def get_game_specific_css(theme: DesignTheme) -> str:
    """Additional CSS for game apps."""
    return f"""
.game-container {{
    text-align: center;
    padding: {theme.spacing.lg};
}}

.score-display {{
    font-size: 48px;
    font-weight: 800;
    color: var(--color-primary);
    margin: {theme.spacing.md} 0;
}}

.game-grid {{
    display: grid;
    gap: {theme.spacing.sm};
    justify-content: center;
    margin: {theme.spacing.lg} auto;
}}

.game-cell {{
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--color-surface);
    border: 2px solid var(--color-border);
    border-radius: {theme.layout.card_radius};
    cursor: pointer;
    transition: all 0.15s ease;
}}

.game-cell:hover {{
    border-color: var(--color-primary);
    background: var(--color-bg);
}}

.game-over {{
    font-size: 32px;
    font-weight: 700;
    color: var(--color-error);
}}

.game-win {{
    color: var(--color-success);
}}
"""


def get_form_specific_css(theme: DesignTheme) -> str:
    """Additional CSS for form-heavy apps."""
    return f"""
.form-group {{
    margin-bottom: {theme.spacing.md};
}}

.form-label {{
    display: block;
    font-weight: 600;
    margin-bottom: {theme.spacing.xs};
    color: var(--color-text);
}}

.form-input {{
    width: 100%;
}}

.form-help {{
    font-size: {theme.typography.font_size_sm};
    color: var(--color-text-muted);
    margin-top: {theme.spacing.xs};
}}

.form-actions {{
    display: flex;
    gap: {theme.spacing.sm};
    margin-top: {theme.spacing.lg};
}}

.form-row {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: {theme.spacing.md};
}}
"""


def get_list_specific_css(theme: DesignTheme) -> str:
    """Additional CSS for list/CRUD apps."""
    return f"""
.item-list {{
    list-style: none;
}}

.item {{
    display: flex;
    align-items: center;
    padding: {theme.spacing.md};
    background: var(--color-surface);
    border-radius: {theme.layout.card_radius};
    margin-bottom: {theme.spacing.sm};
    {"box-shadow: " + theme.layout.shadow + ";" if theme.layout.shadow != "none" else "border: 1px solid var(--color-border);"}
    transition: all 0.15s ease;
}}

.item:hover {{
    {"transform: translateY(-2px); box-shadow: " + theme.layout.shadow.replace("0.1", "0.15") + ";" if theme.layout.shadow != "none" else "border-color: var(--color-primary);"}
}}

.item-content {{
    flex: 1;
}}

.item-title {{
    font-weight: 600;
    color: var(--color-text);
}}

.item-meta {{
    font-size: {theme.typography.font_size_sm};
    color: var(--color-text-muted);
}}

.item-actions {{
    display: flex;
    gap: {theme.spacing.xs};
}}

.empty-state {{
    text-align: center;
    padding: {theme.spacing.xxl};
    color: var(--color-text-muted);
}}
"""


# =============================================================================
# CLI / TESTING
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("App Forge Design System")
    print("=" * 60)
    
    test_descriptions = [
        ("todo list with tasks and due dates", AppCategory.PRODUCTIVITY),
        ("wordle word guessing game", AppCategory.GAME),
        ("budget tracker for managing expenses", AppCategory.FINANCE),
        ("drawing app with canvas", AppCategory.CREATIVE),
        ("flashcard study app for vocabulary", AppCategory.EDUCATION),
        ("fitness workout tracker", AppCategory.HEALTH),
        ("chat messaging app", AppCategory.SOCIAL),
        ("movie recommendation app", AppCategory.ENTERTAINMENT),
        ("password generator tool", AppCategory.UTILITY),
        ("sales dashboard with analytics", AppCategory.DATA),
        ("online shop with products", AppCategory.ECOMMERCE),
    ]
    
    print("\nCategory Detection Test:")
    print("-" * 40)
    
    correct = 0
    for desc, expected in test_descriptions:
        detected = detect_category(desc)
        status = "✓" if detected == expected else "✗"
        if detected == expected:
            correct += 1
        print(f"{status} '{desc[:35]}...' -> {detected.value}")
    
    print(f"\nAccuracy: {correct}/{len(test_descriptions)} ({100*correct//len(test_descriptions)}%)")
    
    print("\n" + "=" * 60)
    print("Theme Preview")
    print("=" * 60)
    
    for category, theme in THEMES.items():
        print(f"\n{category.value.upper()}: {theme.name}")
        print(f"  Primary: {theme.palette.primary}")
        print(f"  Font: {theme.typography.font_family[:30]}...")
        print(f"  Max Width: {theme.layout.max_width}")
        print(f"  Card Radius: {theme.layout.card_radius}")
    
    # Generate sample CSS
    print("\n" + "=" * 60)
    print("Sample CSS (Game Theme)")
    print("=" * 60)
    game_theme = THEMES[AppCategory.GAME]
    css = game_theme.generate_css()
    print(css[:1500] + "...")
