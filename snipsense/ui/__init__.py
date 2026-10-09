"""UI presentation components and stylesheets for SnipSense."""

from snipsense.ui.styles import DARK_THEME_QSS
from snipsense.ui.canvas import SnipCanvas
from snipsense.ui.image_canvas import InteractiveImageCanvas
from snipsense.ui.preview import PreviewWindow
from snipsense.ui.search_modal import SearchModal, SearchResultCard
from snipsense.ui.dedup_dialog import DedupDialog
from snipsense.ui.overlay_hud import OverlayHUD, RecentCaptureCard

__all__ = [
    "DARK_THEME_QSS",
    "SnipCanvas",
    "InteractiveImageCanvas",
    "PreviewWindow",
    "SearchModal",
    "SearchResultCard",
    "DedupDialog",
    "OverlayHUD",
    "RecentCaptureCard",
]
