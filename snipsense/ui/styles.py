"""Central Qt Style Sheets (QSS) and design tokens matching Windows 11 Fluent dark native design."""

DARK_THEME_QSS = """
/* Global Widget Defaults - Windows 11 Fluent Typography */
QWidget {
    background-color: transparent;
    color: #F3F3F3;
    font-family: 'Segoe UI Variable Text', 'Segoe UI', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    font-size: 13px;
    selection-background-color: #0078D4;
    selection-color: #FFFFFF;
}

/* Main Windows & Dialog Shells - Transparent outer shells */
QMainWindow#controlWindow,
QDialog#previewWindow,
QDialog#searchModal,
QDialog#dedupDialog,
QDialog#recordingDialog {
    background-color: transparent;
    border: none;
}

/* Frameless Window Frame Container - Unified Surface Elevation */
QFrame#windowFrame {
    background-color: #202020;
    border: 1px solid #383838;
    border-radius: 8px;
}

/* Custom Titlebar & Frame */
QWidget#customTitleBar {
    background-color: #1C1C1C;
    border-bottom: 1px solid #2B2B2B;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}

QWidget#windowContent {
    background-color: transparent;
}

/* Native Window Control Buttons (Minimize, Expand/Maximize, Close) */
QPushButton#winBtnMinimize, QPushButton#winBtnMaximize {
    background-color: transparent;
    color: #A0A0A0;
    border: none;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 500;
}
QPushButton#winBtnMinimize:hover, QPushButton#winBtnMaximize:hover {
    background-color: rgba(255, 255, 255, 0.08);
    color: #FFFFFF;
}
QPushButton#winBtnMinimize:pressed, QPushButton#winBtnMaximize:pressed {
    background-color: rgba(255, 255, 255, 0.04);
}

QPushButton#winBtnClose {
    background-color: transparent;
    color: #A0A0A0;
    border: none;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 500;
}
QPushButton#winBtnClose:hover {
    background-color: #C42B1C;
    color: #FFFFFF;
}
QPushButton#winBtnClose:pressed {
    background-color: #B82215;
    color: #FFFFFF;
}

/* Frosted Glass Overlay HUD Container */
QFrame#hudContainer {
    background-color: rgba(32, 32, 32, 0.96);
    border: 1px solid #383838;
    border-radius: 8px;
}

/* Hero Action Card (Primary Capture Trigger) - Native Accent Command Button */
QPushButton#heroActionBtn {
    background-color: #0067C0;
    color: #FFFFFF;
    font-size: 13px;
    font-weight: 600;
    border: 1px solid #0078D4;
    border-radius: 6px;
    padding: 10px 16px;
    text-align: left;
}
QPushButton#heroActionBtn:hover {
    background-color: #1170CF;
    border-color: #2680D9;
}
QPushButton#heroActionBtn:pressed {
    background-color: #005A9E;
    border-color: #004578;
}

/* Primary Action Button (Windows 11 Accent Fill) */
QPushButton#primaryAction {
    background-color: #0067C0;
    color: #FFFFFF;
    font-weight: 600;
    font-size: 12px;
    border: 1px solid #0078D4;
    border-radius: 6px;
    padding: 6px 16px;
    min-height: 20px;
}
QPushButton#primaryAction:hover {
    background-color: #1170CF;
    border-color: #2680D9;
}
QPushButton#primaryAction:pressed {
    background-color: #005A9E;
    border-color: #004578;
}
QPushButton#primaryAction:disabled {
    background-color: rgba(255, 255, 255, 0.05);
    color: #666666;
    border-color: #2E2E2E;
}

/* Secondary Ghost Action Button - Native Neutral Control */
QPushButton#ghostAction {
    background-color: #2D2D2D;
    color: #F3F3F3;
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 6px 14px;
    min-height: 20px;
    font-weight: 500;
    font-size: 12px;
}
QPushButton#ghostAction:hover {
    background-color: #383838;
    border-color: #4D4D4D;
    color: #FFFFFF;
}
QPushButton#ghostAction:pressed {
    background-color: #252525;
    border-color: #333333;
}
QPushButton#ghostAction:disabled {
    background-color: rgba(255, 255, 255, 0.03);
    color: #666666;
    border-color: #2B2B2B;
}

/* Compact Tool Card Buttons */
QPushButton#toolCardBtn {
    background-color: #2B2B2B;
    color: #F3F3F3;
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 9px 12px;
    font-size: 12px;
    font-weight: 500;
    text-align: left;
}
QPushButton#toolCardBtn:hover {
    background-color: #353535;
    border-color: #484848;
    color: #FFFFFF;
}
QPushButton#toolCardBtn:pressed {
    background-color: #242424;
    border-color: #333333;
}

/* HUD Quick Action Buttons */
QPushButton#hudActionBtn {
    background-color: #2B2B2B;
    border: 1px solid #383838;
    border-radius: 6px;
    color: #F3F3F3;
    font-size: 12px;
    font-weight: 500;
    text-align: center;
    padding: 9px 12px;
}
QPushButton#hudActionBtn:hover {
    background-color: #353535;
    border-color: #484848;
    color: #FFFFFF;
}
QPushButton#hudActionBtn:pressed {
    background-color: #222222;
}

/* Carousel Card Quick Action Buttons */
QPushButton#cardActionBtn {
    background-color: #2B2B2B;
    border: 1px solid #383838;
    border-radius: 4px;
    color: #F3F3F3;
    font-size: 11px;
    font-weight: 500;
    padding: 3px 8px;
    min-height: 22px;
}
QPushButton#cardActionBtn:hover {
    background-color: #353535;
    border-color: #484848;
    color: #FFFFFF;
}
QPushButton#cardActionBtn:pressed {
    background-color: #222222;
}

/* Carousel Card Frame */
QFrame#carouselCard {
    background-color: #262626;
    border: 1px solid #333333;
    border-radius: 6px;
}
QFrame#carouselCard:hover {
    background-color: #2D2D2D;
    border-color: #444444;
}

/* Shield PII Action Button - Subtle Amber / Warning Restraint */
QPushButton#shieldAction {
    background-color: #2B2B2B;
    color: #F3F3F3;
    font-weight: 500;
    font-size: 12px;
    border: 1px solid #4A4A4A;
    border-radius: 6px;
    padding: 6px 14px;
    min-height: 20px;
}
QPushButton#shieldAction:hover {
    background-color: #353535;
    border-color: #5A5A5A;
}
QPushButton#shieldAction:pressed {
    background-color: #222222;
}

/* Destructive / Close Action */
QPushButton#closeBtn {
    background-color: transparent;
    color: #A0A0A0;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    font-weight: 500;
    font-size: 12px;
}
QPushButton#closeBtn:hover {
    background-color: rgba(255, 255, 255, 0.08);
    color: #FFFFFF;
}
QPushButton#closeBtn:pressed {
    background-color: rgba(255, 255, 255, 0.04);
}

/* Dimension Pill Label */
QLabel#dimensionPill {
    background-color: #262626;
    color: #A0A0A0;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 500;
}

/* Header & Status Labels */
QLabel#headerTitle {
    color: #F3F3F3;
    font-size: 13px;
    font-weight: 600;
}

QLabel#statusBadge {
    background-color: rgba(255, 255, 255, 0.06);
    color: #CCCCCC;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 500;
}

/* Keyboard Shortcut Micro-Badges */
QLabel#kbdBadge {
    background-color: rgba(255, 255, 255, 0.05);
    color: #A0A0A0;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 3px;
    padding: 2px 6px;
    font-size: 10px;
    font-weight: 500;
}

/* Search and Text Input - Native Textbox with Bottom Accent Line on Focus */
QLineEdit#searchInput, QLineEdit#slugEdit {
    background-color: #1A1A1A;
    border: 1px solid #383838;
    border-bottom: 2px solid #555555;
    border-radius: 4px;
    color: #F3F3F3;
    padding: 6px 10px;
    font-size: 12px;
    selection-background-color: #0078D4;
}
QLineEdit#searchInput:focus, QLineEdit#slugEdit:focus {
    border: 1px solid #383838;
    border-bottom: 2px solid #0078D4;
    background-color: #1E1E1E;
}

/* Image Scroll & Preview */
QScrollArea {
    border: 1px solid #333333;
    border-radius: 6px;
    background-color: #141414;
}

/* Native Scrollbars */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #444444;
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #666666;
}

QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 6px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #444444;
    border-radius: 3px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background: #666666;
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

/* Native Tooltip */
QToolTip {
    background-color: #2D2D2D;
    color: #F3F3F3;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}
"""
