"""Central Qt Style Sheets (QSS) and design tokens matching DESIGN.md."""

DARK_THEME_QSS = """
/* Global Widget Defaults */
QWidget {
    background-color: transparent;
    color: #F1F5F9;
    font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
    font-size: 13px;
}

/* Main Preview Window & Dialogs */
QDialog#previewWindow, QWidget#previewContainer {
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

/* Image Scroll & Preview */
QScrollArea {
    border: 1px solid #262E3B;
    border-radius: 8px;
    background-color: #0B0D10;
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
