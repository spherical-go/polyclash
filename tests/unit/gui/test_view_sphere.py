import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from PyQt5.QtGui import QImage

from polyclash.gui.view_sphere import SphereView, ActiveSphereView, PassiveSphereView
from polyclash.gui.constants import stone_empty_color, stone_black_color, stone_white_color
from polyclash.game.board import BLACK, WHITE


# Mock pyvista and vtkmodules
@pytest.fixture
def mock_pyvista():
    with patch('polyclash.gui.view_sphere.pv') as mock_pv:
        # Create mock sphere and mesh objects
        mock_sphere = MagicMock()
        mock_pv.Sphere.return_value = mock_sphere

        # Mock the Qt interactor functionality
        mock_qt_interactor = MagicMock()
        mock_pv.QtInteractor = MagicMock(return_value=mock_qt_interactor)

        yield mock_pv


@pytest.fixture
def mock_mesh():
    with patch('polyclash.gui.view_sphere.mesh') as mock_mesh:
        yield mock_mesh


@pytest.fixture
def mock_face_colors():
    with patch('polyclash.gui.view_sphere.face_colors') as mock_colors:
        yield mock_colors


@pytest.fixture
def mock_cities():
    with patch('polyclash.gui.view_sphere.cities') as mock_cities:
        # Create a list of mock city coordinates for testing
        mock_cities.__iter__.return_value = [
            [1.0, 0.0, 0.0],  # Example city 0
            [0.0, 1.0, 0.0],  # Example city 1
            [0.0, 0.0, 1.0]   # Example city 2
        ]
        mock_cities.__len__.return_value = 3
        yield mock_cities


@pytest.fixture
def mock_city_manager():
    with patch('polyclash.gui.view_sphere.city_manager') as mock_manager:
        mock_manager.find_nearest_city.return_value = 0  # Default return city index
        yield mock_manager


@pytest.fixture
def mock_axis():
    with patch('polyclash.gui.view_sphere.axis') as mock_axis:
        # Define some test axes vectors
        mock_axis.__getitem__.side_effect = lambda idx: np.array([
            [1.0, 0.0, 0.0],  # x-axis
            [0.0, 1.0, 0.0],  # y-axis
            [0.0, 0.0, 1.0],  # z-axis
            [0.0, 0.0, -1.0]  # -z-axis
        ][idx % 4])
        yield mock_axis


class TestSphereView:
    @pytest.fixture
    def sphere_view(self, mock_pv, mock_mesh, mock_face_colors, mock_cities):
        """Create a SphereView for testing."""
        with patch('polyclash.gui.view_sphere.vtkCommand') as mock_vtk_command:
            view = SphereView(parent=None, off_screen=True)
            return view

    def test_init(self, sphere_view, mock_pv, mock_mesh, mock_face_colors, mock_cities):
        """Test SphereView initialization."""
        # Verify that the background color is set
        sphere_view.set_background.assert_called_once_with("darkgray")

        # Verify that the mesh was added
        sphere_view.add_mesh.assert_any_call(
            mock_mesh,
            show_edges=True,
            color="lightblue",
            pickable=False,
            scalars=mock_face_colors,
            rgba=True
        )

        # Verify that 3 city spheres were created (based on our mock)
        assert len(sphere_view.spheres) == 3

    def test_on_reset(self, sphere_view):
        """Test on_reset method."""
        mock_property = MagicMock()
        for actor in sphere_view.spheres.values():
            actor.GetProperty.return_value = mock_property

        sphere_view.on_reset()

        # Verify that all stones are reset to empty color
        for actor in sphere_view.spheres.values():
            actor.GetProperty.assert_called()
            mock_property.SetColor.assert_called_with(
                stone_empty_color[0],
                stone_empty_color[1],
                stone_empty_color[2]
            )

    def test_on_stone_added_black(self, sphere_view):
        """Test on_stone_added method with black stone."""
        point = 1  # Use the second point for this test
        mock_property = MagicMock()
        sphere_view.spheres[point].GetProperty.return_value = mock_property

        sphere_view.on_stone_added(point, BLACK)

        # Verify that the stone color is set to black
        mock_property.SetColor.assert_called_with(
            stone_black_color[0],
            stone_black_color[1],
            stone_black_color[2]
        )

    def test_on_stone_added_white(self, sphere_view):
        """Test on_stone_added method with white stone."""
        point = 2  # Use the third point for this test
        mock_property = MagicMock()
        sphere_view.spheres[point].GetProperty.return_value = mock_property

        sphere_view.on_stone_added(point, WHITE)

        # Verify that the stone color is set to white
        mock_property.SetColor.assert_called_with(
            stone_white_color[0],
            stone_white_color[1],
            stone_white_color[2]
        )

    def test_on_stone_removed(self, sphere_view):
        """Test on_stone_removed method."""
        point = 0  # Use the first point for this test
        mock_property = MagicMock()
        sphere_view.spheres[point].GetProperty.return_value = mock_property

        sphere_view.on_stone_removed(point)

        # Verify that the stone color is reset to empty
        mock_property.SetColor.assert_called_with(
            stone_empty_color[0],
            stone_empty_color[1],
            stone_empty_color[2]
        )

    def test_handle_notification_reset(self, sphere_view):
        """Test handle_notification method with reset message."""
        with patch.object(sphere_view, 'on_reset') as mock_on_reset:
            sphere_view.handle_notification("reset")
            mock_on_reset.assert_called_once()

    def test_handle_notification_add_stone(self, sphere_view):
        """Test handle_notification method with add_stone message."""
        with patch.object(sphere_view, 'on_stone_added') as mock_on_stone_added:
            sphere_view.handle_notification("add_stone", point=1, player=BLACK)
            mock_on_stone_added.assert_called_once_with(1, BLACK)

    def test_handle_notification_remove_stone(self, sphere_view):
        """Test handle_notification method with remove_stone message."""
        with patch.object(sphere_view, 'on_stone_removed') as mock_on_stone_removed:
            sphere_view.handle_notification("remove_stone", point=2)
            mock_on_stone_removed.assert_called_once_with(2)

    def test_change_view(self, sphere_view, mock_axis):
        """Test change_view method."""
        row = 1
        col = 0

        # Mock the camera object
        mock_camera = MagicMock()
        sphere_view.camera = mock_camera

        sphere_view.change_view(row, col)

        # Verify camera position was updated correctly
        np.testing.assert_almost_equal(
            mock_camera.position,
            6 * mock_axis[row + 4 * col]
        )

        # Verify camera focal point is at origin
        np.testing.assert_almost_equal(
            mock_camera.focal_point,
            np.zeros((3))
        )

        # Verify camera view up direction
        np.testing.assert_almost_equal(
            mock_camera.view_up,
            mock_axis[(row + sphere_view.cyclic_pad) % 4 + 4 * col]
        )


class TestActiveSphereView:
    @pytest.fixture
    def mock_controller(self):
        controller = MagicMock()
        controller.board = MagicMock()
        controller.board.register_observer = MagicMock()
        controller.side = BLACK
        return controller

    @pytest.fixture
    def mock_overlay_info(self):
        overlay = MagicMock()
        overlay.update = MagicMock()
        return overlay

    @pytest.fixture
    def mock_overlay_map(self):
        overlay = MagicMock()
        overlay.set_sphere_view = MagicMock()
        overlay.columns = 2
        overlay.rows = 4
        return overlay

    @pytest.fixture
    def mock_status_bar(self):
        status_bar = MagicMock()
        status_bar.showMessage = MagicMock()
        return status_bar

    @pytest.fixture
    def active_view(self, mock_pv, mock_mesh, mock_face_colors, mock_cities,
                    mock_controller, mock_overlay_info, mock_overlay_map, mock_status_bar):
        """Create an ActiveSphereView for testing."""
        with patch('polyclash.gui.view_sphere.PassiveSphereView') as MockPassiveSphereView:
            mock_passive = MagicMock()
            MockPassiveSphereView.return_value = mock_passive

            view = ActiveSphereView(
                parent=None,
                controller=mock_controller,
                status_bar=mock_status_bar,
                overlay_info=mock_overlay_info,
                overlay_map=mock_overlay_map
            )
            return view

    def test_init(self, active_view, mock_controller, mock_overlay_map):
        """Test ActiveSphereView initialization."""
        # Verify that overlay_map was connected to this view
        mock_overlay_map.set_sphere_view.assert_called_once_with(active_view)

        # Verify that axes were added
        active_view.add_axes.assert_called_once_with(interactive=True)

        # Verify that hidden (passive) view was created and registered with the board
        assert active_view.hidden is not None
        mock_controller.board.register_observer.assert_called_once_with(active_view.hidden)

    def test_setup_scene(self, active_view):
        """Test setup_scene method."""
        # Reset the mocks to test the setup_scene call
        active_view.interactor = MagicMock()
        active_view.interactor.GetRenderWindow.return_value.GetInteractor.return_value.CreateDefaultPicker.return_value = MagicMock()
        active_view.picker = None

        active_view.setup_scene()

        # Verify the picker was created
        assert active_view.picker is not None

        # Verify event observer was added
        active_view.interactor.AddObserver.assert_called_once()

    def test_on_player_switched_enabled(self, active_view, mock_controller):
        """Test on_player_switched method with controller side."""
        # Set the side to match the controller
        active_view.picker_enabled = False
        active_view.on_player_switched(mock_controller.side)

        # Verify picker is enabled when it's the player's turn
        assert active_view.picker_enabled is True

    def test_on_player_switched_disabled(self, active_view, mock_controller):
        """Test on_player_switched method with opposite side."""
        # Set the side to opposite of controller
        active_view.picker_enabled = True
        active_view.on_player_switched(WHITE if mock_controller.side == BLACK else BLACK)

        # Verify picker is disabled when it's not the player's turn
        assert active_view.picker_enabled is False

    def test_update_active(self, active_view, mock_overlay_info):
        """Test update method when window is active."""
        active_view.isActiveWindow = MagicMock(return_value=True)
        active_view.update_maps_view = MagicMock()

        active_view.update()

        # Verify that maps view is updated
        active_view.update_maps_view.assert_called_once()

        # Verify that overlay info is updated
        mock_overlay_info.update.assert_called_once()

    def test_left_button_press_event_disabled(self, active_view):
        """Test left_button_press_event when picker is disabled."""
        active_view.picker_enabled = False
        active_view.interactor = MagicMock()
        active_view.picker = MagicMock()

        active_view.left_button_press_event(None, None)

        # Verify that no interaction happens when picker is disabled
        active_view.interactor.GetEventPosition.assert_not_called()
        active_view.picker.Pick.assert_not_called()

    def test_left_button_press_event_enabled(self, active_view, mock_controller, mock_city_manager):
        """Test left_button_press_event when picker is enabled."""
        active_view.picker_enabled = True
        active_view.interactor = MagicMock()
        active_view.interactor.GetEventPosition.return_value = (100, 200)
        active_view.picker = MagicMock()
        active_view.renderer = MagicMock()

        # Mock that something was picked
        picked_actor = MagicMock()
        picked_actor.GetCenter.return_value = (1.0, 0.0, 0.0)
        active_view.picker.GetActor.return_value = picked_actor

        # Call the event handler
        active_view.left_button_press_event(None, None)

        # Verify that GetEventPosition was called
        active_view.interactor.GetEventPosition.assert_called_once()

        # Verify that Pick was called with right parameters
        active_view.picker.Pick.assert_called_once_with(100, 200, 0, active_view.renderer)

        # Verify the controller was called to play at the target city
        mock_controller.player_played.assert_called_once_with(0)  # The city index from our mock

    def test_update_maps_view(self, active_view, mock_overlay_map):
        """Test update_maps_view method."""
        # Create a mock for hidden (PassiveSphereView)
        mock_hidden = MagicMock()
        mock_hidden.change_view = MagicMock()
        mock_hidden.capture_view = MagicMock(return_value=QImage())
        active_view.hidden = mock_hidden

        active_view.update_maps_view()

        # Verify the view is changed and captured for each grid cell
        expected_calls = mock_overlay_map.rows * mock_overlay_map.columns
        assert mock_hidden.change_view.call_count == expected_calls
        assert mock_hidden.capture_view.call_count == expected_calls

        # Verify each image is set in the overlay map
        assert mock_overlay_map.set_image.call_count == expected_calls


class TestPassiveSphereView:
    @pytest.fixture
    def passive_view(self, mock_pv, mock_mesh, mock_face_colors, mock_cities):
        """Create a PassiveSphereView for testing."""
        view = PassiveSphereView()
        return view

    def test_init(self, passive_view):
        """Test PassiveSphereView initialization."""
        # Verify that the view is constructed with off_screen=True
        passive_view.__init__.assert_called_with(None, off_screen=True)

    def test_capture_view(self, passive_view):
        """Test capture_view method."""
        # Mock the screenshot method
        test_img = np.zeros((10, 10, 4), dtype=np.uint8)
        passive_view.screenshot.return_value = test_img

        with patch('polyclash.gui.view_sphere.qimage') as mock_qimage:
            mock_qimage.return_value = QImage()
            result = passive_view.capture_view()

            # Verify screenshot was called with right parameters
            passive_view.screenshot.assert_called_once_with(
                transparent_background=True,
                return_img=True,
                scale=2
            )

            # Verify qimage was called with the screenshot result
            mock_qimage.assert_called_once_with(test_img)

            # Verify a QImage is returned
            assert isinstance(result, QImage)
