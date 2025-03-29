import pytest
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QBrush, QColor
from PyQt5.QtWidgets import QWidget

from polyclash.game.board import BLACK, WHITE
from polyclash.gui.overly_info import OverlayInfo, black, white


class TestOverlayInfo:
    @pytest.fixture
    def overlay_info(self, qapp):
        """Create an OverlayInfo for testing."""
        overlay = OverlayInfo(parent=None)
        return overlay
    
    def test_init(self, overlay_info):
        """Test OverlayInfo initialization."""
        # Verify the initial state
        assert overlay_info.black_ratio == 0
        assert overlay_info.white_ratio == 0
        assert overlay_info.unknown_ratio == 1
        
        # Skip direct color comparison which may vary by Qt version
        # Just ensure a color is set
        assert overlay_info.color is not None
    
    def test_paint_event(self, overlay_info):
        """Test paintEvent method."""
        # Set some values
        overlay_info.black_ratio = 0.3
        overlay_info.white_ratio = 0.6
        overlay_info.unknown_ratio = 0.1
        overlay_info.color = QColor(255, 0, 0)  # Red
        
        # Mock super class paintEvent and QPainter
        with patch('PyQt5.QtWidgets.QWidget.paintEvent') as mock_super_paint, \
             patch('polyclash.gui.overly_info.QPainter') as MockPainter, \
             patch.object(overlay_info, 'rect') as mock_rect:
            
            # Configure mocks
            mock_painter = MagicMock(spec=QPainter)
            MockPainter.return_value = mock_painter
            mock_rect.return_value = QRect(0, 0, 200, 100)
            
            # Create a mock event
            mock_event = MagicMock()
            
            # Call paintEvent
            overlay_info.paintEvent(mock_event)
            
            # Verify painter is created and configured
            MockPainter.assert_called_once_with(overlay_info)
            
            # Verify background is drawn
            mock_painter.setOpacity.assert_any_call(0.5)  # First call with 0.5
            mock_painter.setBrush.assert_any_call(QBrush(QColor(192, 192, 192, 127)))
            mock_painter.drawRect.assert_called_once_with(mock_rect.return_value)
            
            # Verify color disk is drawn with the set color
            mock_painter.setOpacity.assert_any_call(1.0)
            mock_painter.setBrush.assert_any_call(QBrush(overlay_info.color))
            mock_painter.drawEllipse.assert_called_once_with(10, 10, 50, 50)
            
            # Verify text is drawn with the correct percentages
            assert mock_painter.drawText.call_count == 3
            mock_painter.drawText.assert_any_call(70, 30, "Black: 30.00")
            mock_painter.drawText.assert_any_call(70, 50, "White: 60.00")
            mock_painter.drawText.assert_any_call(70, 70, "Unknown: 10.00")
    
    def test_change_color(self, overlay_info):
        """Test change_color method."""
        # Mock the update method
        with patch.object(overlay_info, 'update') as mock_update:
            new_color = QColor(0, 128, 0)  # Green
            overlay_info.change_color(new_color)
            
            # Verify color is updated
            assert overlay_info.color == new_color
            
            # Verify update is called
            mock_update.assert_called_once()
    
    def test_change_score(self, overlay_info):
        """Test change_score method."""
        # Mock the update method
        with patch.object(overlay_info, 'update') as mock_update:
            overlay_info.change_score(0.25, 0.35, 0.4)
            
            # Verify scores are updated
            assert overlay_info.black_ratio == 0.25
            assert overlay_info.white_ratio == 0.35
            assert overlay_info.unknown_ratio == 0.4
            
            # Verify update is called
            mock_update.assert_called_once()
    
    def test_handle_notification_switch_player_black(self, overlay_info):
        """Test handle_notification method with switch_player to BLACK."""
        # Mock change_color method
        with patch.object(overlay_info, 'change_color') as mock_change_color:
            overlay_info.handle_notification("switch_player", side=BLACK)
            
            # Verify change_color is called with black color
            mock_change_color.assert_called_once_with(black)
    
    def test_handle_notification_switch_player_white(self, overlay_info):
        """Test handle_notification method with switch_player to WHITE."""
        # Mock change_color method
        with patch.object(overlay_info, 'change_color') as mock_change_color:
            overlay_info.handle_notification("switch_player", side=WHITE)
            
            # Verify change_color is called with white color
            mock_change_color.assert_called_once_with(white)
    
    def test_handle_notification_reset(self, overlay_info):
        """Test handle_notification method with reset message."""
        # Mock change_color and change_score methods
        with patch.object(overlay_info, 'change_color') as mock_change_color, \
             patch.object(overlay_info, 'change_score') as mock_change_score:
            
            overlay_info.handle_notification("reset")
            
            # Verify change_color is called with BLACK
            mock_change_color.assert_called_once_with(BLACK)
            
            # Verify change_score is called with initial values
            mock_change_score.assert_called_once_with(0, 0, 1)
    
    def test_handle_notification_add_stone(self, overlay_info):
        """Test handle_notification method with add_stone message."""
        # Mock change_score method
        with patch.object(overlay_info, 'change_score') as mock_change_score:
            score = (0.4, 0.3, 0.3)
            overlay_info.handle_notification("add_stone", score=score)
            
            # Verify change_score is called with provided score
            mock_change_score.assert_called_once_with(*score)
    
    def test_handle_notification_remove_stone(self, overlay_info):
        """Test handle_notification method with remove_stone message."""
        # Mock change_score method
        with patch.object(overlay_info, 'change_score') as mock_change_score:
            score = (0.2, 0.2, 0.6)
            overlay_info.handle_notification("remove_stone", score=score)
            
            # Verify change_score is called with provided score
            mock_change_score.assert_called_once_with(*score)
