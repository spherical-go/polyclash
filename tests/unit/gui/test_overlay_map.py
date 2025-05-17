import pytest
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QBrush, QColor, QImage
from PyQt5.QtWidgets import QWidget
from PyQt5.QtTest import QTest

from polyclash.gui.overly_map import OverlayMap


class TestOverlayMap:
    @pytest.fixture
    def overlay_map(self, qapp):
        """Create an OverlayMap for testing."""
        overlay = OverlayMap(parent=None, rows=2, columns=3)
        return overlay
    
    def test_init(self, overlay_map):
        """Test OverlayMap initialization."""
        # Verify the initial state
        assert overlay_map.rows == 2
        assert overlay_map.columns == 3
        assert len(overlay_map.images) == 2
        assert all(len(row) == 3 for row in overlay_map.images)
        assert all(image is None for row in overlay_map.images for image in row)
        assert len(overlay_map.scaled_images) == 2
        assert all(len(row) == 3 for row in overlay_map.scaled_images)
        assert all(image is None for row in overlay_map.scaled_images for image in row)
        assert overlay_map.last_width == 0
        assert overlay_map.last_height == 0
        assert overlay_map.sphere_view is None
        
        # Verify mouse tracking is enabled
        assert overlay_map.hasMouseTracking()
    
    def test_set_image(self, overlay_map):
        """Test set_image method."""
        # Create a mock image
        mock_image = MagicMock(spec=QImage)
        
        # Call set_image with valid indices
        with patch.object(overlay_map, 'update') as mock_update:
            overlay_map.set_image(1, 2, mock_image)
            
            # Verify the image was stored
            assert overlay_map.images[1][2] is mock_image
            # Verify the scaled image was invalidated
            assert overlay_map.scaled_images[1][2] is None
            # Verify update was called
            mock_update.assert_called_once()
    
    def test_set_image_invalid_indices(self, overlay_map):
        """Test set_image method with invalid indices."""
        # Create a mock image
        mock_image = MagicMock(spec=QImage)
        
        # Call set_image with invalid indices
        with patch.object(overlay_map, 'update') as mock_update:
            overlay_map.set_image(5, 5, mock_image)  # Out of bounds
            
            # Verify nothing changed and update wasn't called
            assert all(image is None for row in overlay_map.images for image in row)
            mock_update.assert_not_called()
    
    def test_resize_event(self, overlay_map):
        """Test resizeEvent method."""
        # Set initial dimensions
        overlay_map.last_width = 100
        overlay_map.last_height = 200
        
        # Add a scaled image to verify it gets invalidated
        mock_image = MagicMock(spec=QImage)
        overlay_map.scaled_images[0][0] = mock_image
        
        # Create a mock resize event
        mock_event = MagicMock()
        
        # Mock the width and height methods
        overlay_map.width = MagicMock(return_value=150)
        overlay_map.height = MagicMock(return_value=250)
        
        with patch.object(overlay_map, 'update') as mock_update:
            overlay_map.resizeEvent(mock_event)
            
            # Verify dimensions were updated
            assert overlay_map.last_width == 150
            assert overlay_map.last_height == 250
            
            # Verify scaled images were invalidated
            assert all(image is None for row in overlay_map.scaled_images for image in row)
            
            # Verify update was called
            mock_update.assert_called_once()
    
    def test_resize_event_same_size(self, overlay_map):
        """Test resizeEvent method when size doesn't change."""
        # Set initial dimensions
        overlay_map.last_width = 100
        overlay_map.last_height = 200
        
        # Add a scaled image to verify it doesn't get invalidated
        mock_image = MagicMock(spec=QImage)
        overlay_map.scaled_images[0][0] = mock_image
        
        # Create a mock resize event
        mock_event = MagicMock()
        
        # Mock the width and height methods to return the same size
        overlay_map.width = MagicMock(return_value=100)
        overlay_map.height = MagicMock(return_value=200)
        
        with patch.object(overlay_map, 'update') as mock_update:
            overlay_map.resizeEvent(mock_event)
            
            # Verify scaled images were not invalidated
            assert overlay_map.scaled_images[0][0] is mock_image
            
            # Verify update was not called
            mock_update.assert_not_called()
    
    def test_paint_event(self, overlay_map):
        """Test paintEvent method."""
        # Mock super class paintEvent
        with patch('PyQt5.QtWidgets.QWidget.paintEvent') as mock_super_paint, \
             patch('polyclash.gui.overly_map.QPainter') as MockPainter, \
             patch.object(overlay_map, 'rect') as mock_rect:
            
            # Configure mocks
            mock_painter = MagicMock(spec=QPainter)
            MockPainter.return_value = mock_painter
            mock_rect.return_value = QRect(0, 0, 300, 200)
            
            # Set up width and height
            overlay_map.width = MagicMock(return_value=300)
            overlay_map.height = MagicMock(return_value=200)
            
            # Create a mock image and scaled image
            mock_image = MagicMock(spec=QImage)
            mock_scaled_image = MagicMock(spec=QImage)
            
            # Set up one of the images
            overlay_map.images[0][1] = mock_image
            mock_image.scaled.return_value = mock_scaled_image
            
            # Create a mock event
            mock_event = MagicMock()
            
            # Call paintEvent
            overlay_map.paintEvent(mock_event)
            
            # Verify super was called
            mock_super_paint.assert_called_once_with(mock_event)
            
            # Verify painter was created and set up
            MockPainter.assert_called_once_with(overlay_map)
            mock_painter.setOpacity.assert_any_call(0.5)  # First call with 0.5
            mock_painter.setBrush.assert_called_once()
            mock_painter.drawRect.assert_called_once_with(mock_rect.return_value)
            
            # Verify image scaling and drawing
            mock_image.scaled.assert_called_once()
            mock_painter.drawImage.assert_called_once()
            
            # Verify opacity was reset to 1.0
            mock_painter.setOpacity.assert_any_call(1.0)
    
    def test_mouse_press_event(self, overlay_map):
        """Test mousePressEvent method."""
        # Mock the width, height and trigger_view_change methods
        overlay_map.width = MagicMock(return_value=300)
        overlay_map.height = MagicMock(return_value=200)
        overlay_map.trigger_view_change = MagicMock()
        
        # Create a mock event at position (160, 70)
        mock_event = MagicMock()
        mock_event.x.return_value = 160
        mock_event.y.return_value = 70
        
        # Call mousePressEvent
        overlay_map.mousePressEvent(mock_event)
        
        # Calculate expected row and column
        # With width=300 and 3 columns, each column is 100px wide
        # With height=200 and 2 rows, each row is 100px high
        # Position (160, 70) should be at row=0, col=1
        expected_row = 0
        expected_col = 1
        
        # Verify trigger_view_change was called with correct coordinates
        overlay_map.trigger_view_change.assert_called_once_with(expected_row, expected_col)
    
    def test_set_sphere_view(self, overlay_map):
        """Test set_sphere_view method."""
        mock_sphere_view = MagicMock()
        
        overlay_map.set_sphere_view(mock_sphere_view)
        
        assert overlay_map.sphere_view is mock_sphere_view
    
    def test_trigger_view_change(self, overlay_map):
        """Test trigger_view_change method."""
        # Create a mock sphere_view
        mock_sphere_view = MagicMock()
        overlay_map.sphere_view = mock_sphere_view
        
        # Call trigger_view_change
        overlay_map.trigger_view_change(1, 2)
        
        # Verify sphere_view.change_view was called with correct coordinates
        mock_sphere_view.change_view.assert_called_once_with(1, 2)
    
    def test_trigger_view_change_no_sphere_view(self, overlay_map):
        """Test trigger_view_change method when sphere_view is None."""
        # Ensure sphere_view is None
        overlay_map.sphere_view = None
        
        # Call trigger_view_change - should not raise any exception
        overlay_map.trigger_view_change(1, 2)
