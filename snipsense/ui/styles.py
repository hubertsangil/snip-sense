"""Central Qt Style Sheets (QSS) and design tokens matching DESIGN.md."""

DARK_THEME_QSS = """
/* Global Widget Defaults */
QWidget {
    background-color: transparent;
    color: #F1F5F9;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}

/* Main Preview Window & Dialogs */
QMainWindow#controlWindow, QWidget#controlCentral,
QDialog#previewWindow, QWidget#previewContainer,
QDialog#searchModal, QWidget#searchContainer,
QDialog#dedupDialog, QWidget#dedupContainer {
    background-color: #14181F;
    border: 1px solid #262E3B;
    border-radius: 12px;
}

/* Frosted Glass Overlay HUD Container */
QFrame#hudContainer {
    background-color: #14181F;
    border: 1px solid #262E3B;
    border-radius: 12px;
}

/* Primary Action Button (Emerald) */
QPushButton#primaryAction {
    background-color: #10B981;
    color: #0B0D10;
    font-weight: 600;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    min-height: 18px;
}
QPushButton#primaryAction:hover {
    background-color: #059669;
}
QPushButton#primaryAction:pressed {
    background-color: #047857;
}

/* Secondary Ghost Action Button */
QPushButton#ghostAction {
    background-color: #1D232D;
    color: #F1F5F9;
    border: 1px solid #262E3B;
    border-radius: 6px;
    padding: 7px 14px;
    min-height: 18px;
}
QPushButton#ghostAction:hover {
    background-color: #2A3342;
    border-color: #3B82F6;
}
QPushButton#ghostAction:pressed {
    background-color: #1A202C;
}

/* HUD Quick Action Buttons */
QPushButton#hudActionBtn {
    background-color: #1A202C;
    border: 1px solid #2D3748;
    border-radius: 8px;
    color: #F1F5F9;
    font-size: 12px;
    font-weight: 600;
    text-align: center;
    padding: 8px 12px;
}
QPushButton#hudActionBtn:hover {
    background-color: #242D3D;
    border-color: #3B82F6;
    color: #FFFFFF;
}
QPushButton#hudActionBtn:pressed {
    background-color: #14181F;
}

/* Carousel Card Quick Action Buttons */
QPushButton#cardActionBtn {
    background-color: #1A202C;
    border: 1px solid #2D3748;
    border-radius: 4px;
    color: #F1F5F9;
    font-size: 11px;
    font-weight: 500;
    padding: 3px 6px;
    min-height: 22px;
}
QPushButton#cardActionBtn:hover {
    background-color: #2D3748;
    border-color: #3B82F6;
    color: #FFFFFF;
}
QPushButton#cardActionBtn:pressed {
    background-color: #14181F;
}

/* Carousel Card Frame */
QFrame#carouselCard {
    background-color: #14181F;
    border: 1px solid #262E3B;
    border-radius: 10px;
}
QFrame#carouselCard:hover {
    background-color: #1D232D;
    border-color: #3B82F6;
}

/* Shield PII Action Button (Indigo / Violet with prominent accent) */
QPushButton#shieldAction {
    background-color: #4F46E5;
    color: #FFFFFF;
    font-weight: 600;
    border: 1px solid #6366F1;
    border-radius: 6px;
    padding: 7px 14px;
    min-height: 18px;
}
QPushButton#shieldAction:hover {
    background-color: #4338CA;
    border-color: #818CF8;
}
QPushButton#shieldAction:pressed {
    background-color: #3730A3;
}

/* Destructive / Close Action */
QPushButton#closeBtn {
    background-color: transparent;
    color: #94A3B8;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    font-weight: bold;
}
QPushButton#closeBtn:hover {
    background-color: rgba(244, 63, 94, 0.2);
    color: #F43F5E;
}

/* Dimension Pill Label */
QLabel#dimensionPill {
    background-color: rgba(11, 13, 16, 0.85);
    color: #F1F5F9;
    border: 1px solid #262E3B;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}

/* Header & Status Labels */
QLabel#headerTitle {
    color: #F1F5F9;
    font-size: 14px;
    font-weight: 600;
}

QLabel#statusBadge {
    background-color: rgba(16, 185, 129, 0.15);
    color: #10B981;
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 11px;
    font-weight: 600;
}

/* Search and Text Input */
QLineEdit#searchInput, QLineEdit#slugEdit {
    background-color: #0B0D10;
    border: 1px solid #262E3B;
    border-radius: 6px;
    color: #F1F5F9;
    padding: 6px 10px;
    selection-background-color: #3B82F6;
}
QLineEdit#searchInput:focus, QLineEdit#slugEdit:focus {
    border: 1px solid #3B82F6;
}

/* Image Scroll & Preview */
QScrollArea {
    border: 1px solid #262E3B;
    border-radius: 8px;
    background-color: #0B0D10;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #0B0D10;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #262E3B;
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #3B82F6;
}

QScrollBar:horizontal {
    border: none;
    background: #0B0D10;
    height: 6px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #262E3B;
    border-radius: 3px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background: #3B82F6;
}

/* Tooltip */
QToolTip {
    background-color: #14181F;
    color: #F1F5F9;
    border: 1px solid #262E3B;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}
"""
