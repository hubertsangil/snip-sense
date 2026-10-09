"""Central Qt Style Sheets (QSS) and design tokens matching DESIGN.md."""

DARK_THEME_QSS = """
/* Global Widget Defaults */
QWidget {
    background-color: transparent;
    color: #F8FAFC;
    font-family: 'Segoe UI Variable Display', 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
    font-size: 13px;
    selection-background-color: #3B82F6;
    selection-color: #FFFFFF;
}

/* Main Windows & Dialog Shells */
QMainWindow#controlWindow, QWidget#controlCentral,
QDialog#previewWindow, QWidget#previewContainer,
QDialog#searchModal, QWidget#searchContainer,
QDialog#dedupDialog, QWidget#dedupContainer,
QDialog#recordingDialog, QWidget#recordingContainer {
    background-color: #0E1218;
    border: 1px solid #1E2633;
    border-radius: 14px;
}

/* Frosted Glass Overlay HUD Container */
QFrame#hudContainer {
    background-color: #121620;
    border: 1px solid #232C3B;
    border-radius: 14px;
}

/* Hero Action Card (Primary Capture Trigger) */
QPushButton#heroActionBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #10B981, stop:1 #059669);
    color: #04120D;
    font-size: 13px;
    font-weight: 700;
    border: 1px solid #34D399;
    border-radius: 10px;
    padding: 10px 16px;
    text-align: left;
}
QPushButton#heroActionBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #34D399, stop:1 #10B981);
    border-color: #6EE7B7;
}
QPushButton#heroActionBtn:pressed {
    background: #047857;
    border-color: #059669;
}

/* Primary Action Button (Emerald) */
QPushButton#primaryAction {
    background-color: #10B981;
    color: #05130E;
    font-weight: 600;
    font-size: 12px;
    border: 1px solid #34D399;
    border-radius: 8px;
    padding: 7px 16px;
    min-height: 20px;
}
QPushButton#primaryAction:hover {
    background-color: #059669;
    border-color: #6EE7B7;
}
QPushButton#primaryAction:pressed {
    background-color: #047857;
    border-color: #059669;
}

/* Secondary Ghost Action Button */
QPushButton#ghostAction {
    background-color: #151A24;
    color: #F1F5F9;
    border: 1px solid #232C3B;
    border-radius: 8px;
    padding: 7px 14px;
    min-height: 20px;
    font-weight: 500;
    font-size: 12px;
}
QPushButton#ghostAction:hover {
    background-color: #1D2433;
    border-color: #3B82F6;
    color: #FFFFFF;
}
QPushButton#ghostAction:pressed {
    background-color: #11151E;
    border-color: #232C3B;
}

/* Compact Tool Card Buttons */
QPushButton#toolCardBtn {
    background-color: #131822;
    color: #E2E8F0;
    border: 1px solid #1F2736;
    border-radius: 9px;
    padding: 8px 12px;
    font-size: 12px;
    font-weight: 600;
    text-align: left;
}
QPushButton#toolCardBtn:hover {
    background-color: #1A2130;
    border-color: #3B82F6;
    color: #FFFFFF;
}
QPushButton#toolCardBtn:pressed {
    background-color: #10141D;
    border-color: #1F2736;
}

/* HUD Quick Action Buttons */
QPushButton#hudActionBtn {
    background-color: #161C26;
    border: 1px solid #252F3E;
    border-radius: 9px;
    color: #F8FAFC;
    font-size: 12px;
    font-weight: 600;
    text-align: center;
    padding: 9px 12px;
}
QPushButton#hudActionBtn:hover {
    background-color: #1E2634;
    border-color: #3B82F6;
    color: #FFFFFF;
}
QPushButton#hudActionBtn:pressed {
    background-color: #12161F;
}

/* Carousel Card Quick Action Buttons */
QPushButton#cardActionBtn {
    background-color: #161C26;
    border: 1px solid #252F3E;
    border-radius: 6px;
    color: #F8FAFC;
    font-size: 11px;
    font-weight: 500;
    padding: 3px 8px;
    min-height: 22px;
}
QPushButton#cardActionBtn:hover {
    background-color: #232B3B;
    border-color: #3B82F6;
    color: #FFFFFF;
}
QPushButton#cardActionBtn:pressed {
    background-color: #12161F;
}

/* Carousel Card Frame */
QFrame#carouselCard {
    background-color: #121721;
    border: 1px solid #202837;
    border-radius: 10px;
}
QFrame#carouselCard:hover {
    background-color: #171E2B;
    border-color: #3B82F6;
}

/* Shield PII Action Button (Indigo / Violet with prominent accent) */
QPushButton#shieldAction {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4F46E5, stop:1 #4338CA);
    color: #FFFFFF;
    font-weight: 600;
    font-size: 12px;
    border: 1px solid #6366F1;
    border-radius: 8px;
    padding: 7px 14px;
    min-height: 20px;
}
QPushButton#shieldAction:hover {
    background: #4338CA;
    border-color: #818CF8;
}
QPushButton#shieldAction:pressed {
    background: #3730A3;
}

/* Destructive / Close Action */
QPushButton#closeBtn {
    background-color: transparent;
    color: #94A3B8;
    border: none;
    border-radius: 6px;
    padding: 4px 8px;
    font-weight: 600;
    font-size: 13px;
}
QPushButton#closeBtn:hover {
    background-color: rgba(244, 63, 94, 0.15);
    color: #F43F5E;
}
QPushButton#closeBtn:pressed {
    background-color: rgba(244, 63, 94, 0.25);
}

/* Dimension Pill Label */
QLabel#dimensionPill {
    background-color: #121721;
    color: #94A3B8;
    border: 1px solid #222B3A;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 600;
}

/* Header & Status Labels */
QLabel#headerTitle {
    color: #F8FAFC;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: -0.2px;
}

QLabel#statusBadge {
    background-color: rgba(16, 185, 129, 0.12);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.28);
    border-radius: 9999px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}

/* Keyboard Shortcut Micro-Badges */
QLabel#kbdBadge {
    background-color: rgba(255, 255, 255, 0.06);
    color: #94A3B8;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 10px;
    font-weight: 600;
}

/* Search and Text Input */
QLineEdit#searchInput, QLineEdit#slugEdit {
    background-color: #0A0D13;
    border: 1px solid #202736;
    border-radius: 8px;
    color: #F8FAFC;
    padding: 7px 12px;
    font-size: 12px;
    selection-background-color: #3B82F6;
}
QLineEdit#searchInput:focus, QLineEdit#slugEdit:focus {
    border: 1px solid #3B82F6;
    background-color: #0D111A;
}

/* Image Scroll & Preview */
QScrollArea {
    border: 1px solid #1E2633;
    border-radius: 10px;
    background-color: #0A0D13;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #0A0D13;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #232C3B;
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #3B82F6;
}

QScrollBar:horizontal {
    border: none;
    background: #0A0D13;
    height: 6px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #232C3B;
    border-radius: 3px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background: #3B82F6;
}

/* List Widget & Items (Search Modal) */
QListWidget#resultsList {
    background-color: transparent;
    border: none;
    outline: none;
}
QListWidget#resultsList::item {
    background-color: transparent;
    border: none;
    padding: 2px 0px;
}
QListWidget#resultsList::item:selected {
    background-color: transparent;
}

/* Tooltip */
QToolTip {
    background-color: #121721;
    color: #F8FAFC;
    border: 1px solid #232C3B;
    border-radius: 6px;
    padding: 5px 9px;
    font-size: 11px;
}
"""
