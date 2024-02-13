import pytest
import unittest.mock
import math

import sys
sys.path.append('..')

from server import BouncingBallTrack, display_error
from av import VideoFrame

@pytest.mark.asyncio
async def test_bouncing_ball_track():
    ball_track = BouncingBallTrack()

    # Check if recv method returns a VideoFrame
    frame = await ball_track.recv()
    assert frame is not None
    assert isinstance(frame, VideoFrame)

    # Check if the ball position is updated after receiving a frame
    assert ball_track.x != 0
    assert ball_track.y != 0

    # Check if the ball bounces off the walls
    ball_track.x = ball_track.width - ball_track.ball_radius - 5
    ball_track.velocity_x = 5
    await ball_track.recv()
    assert ball_track.velocity_x == -5

    ball_track.y = ball_track.height - ball_track.ball_radius - 3
    ball_track.velocity_y = 3
    await ball_track.recv()
    assert ball_track.velocity_y == -3

@pytest.mark.print_check
def test_display_error():
    original_coords = (10, 20)
    received_coords = (12, 18)
    error = math.sqrt((received_coords[0] - original_coords[0])**2 + (received_coords[1] - original_coords[1])**2)

    # Mocking print to capture the output
    with unittest.mock.patch('builtins.print') as mock_print:
        display_error(original_coords, received_coords)

    # Check if the correct messages are printed
    expected_calls = [
        unittest.mock.call(f"Original Coordinates: {original_coords}"),
        unittest.mock.call(f"Received Coordinates: {received_coords}"),
        unittest.mock.call(f"Error between coordinates: {error}"),
        unittest.mock.call("\n"),
    ]

    assert mock_print.call_args_list == expected_calls
