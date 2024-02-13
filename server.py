import os
import argparse
import asyncio

import cv2
import numpy as np
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
)
from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling
from av import VideoFrame
import json
import math


class BouncingBallTrack(VideoStreamTrack):
    """
    A video track that returns a bouncing ball.
    """

    def __init__(self):
        """
        Initialize the BouncingBallTrack.

        Sets up the initial parameters for the bouncing ball.
        """
        super().__init__()  # don't forget this!
        self.width = 400
        self.height = 300
        self.ball_radius = 20
        self.ball_color = (0, 0, 255)

        self.x = self.ball_radius + 5
        self.y = self.height // 2
        self.velocity_x = 5
        self.velocity_y = 3 

        self.original_coords = {}

    async def recv(self):
        """
        Receive a video frame with a bouncing ball.

        Updates the ball position, draws it on the image, and handles ball bouncing off walls.

        Returns:
            VideoFrame: The generated video frame.
        """
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Update the ball position
        self.x += self.velocity_x
        self.y += self.velocity_y

        # Draw the ball on the image
        cv2.circle(img, (int(self.x), int(self.y)), self.ball_radius, self.ball_color, -1)

        # Bounce the ball off the walls
        if self.x - self.ball_radius < 0 or self.x + self.ball_radius >= self.width:
            self.velocity_x = -self.velocity_x
        if self.y - self.ball_radius < 0 or self.y + self.ball_radius >= self.height:
            self.velocity_y = -self.velocity_y

        frame = VideoFrame.from_ndarray(
                    img, format="bgr24"
                )
        pts, time_base = await self.next_timestamp()

        frame.pts = pts
        frame.time_base = time_base
        self.original_coords[frame.pts] = (self.x, self.y)
        return frame
    


def display_error(original_coords, received_coords):
    """
    Display the error between original and received coordinates.

    Args:
        original_coords (tuple): The original coordinates (x, y).
        received_coords (tuple): The received coordinates (x, y).
    """
    x1, y1 = original_coords
    x2, y2 = received_coords
    print(f"Original Coordinates: {original_coords}")
    print(f"Received Coordinates: {received_coords}")

    error = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    print(f"Error between coordinates: {error}")
    print("\n")


async def run(pc, signaling):
    """
    Run the main event loop for the video streaming.

    Args:
        pc (RTCPeerConnection): The RTCPeerConnection for communication.
        signaling: The signaling mechanism for communication.
    """
    ballTrack = BouncingBallTrack()

    @pc.on("datachannel")
    async def on_datachannel(channel):
        """
        Handle the creation of a data channel.

        Args:
            channel: The data channel for communication.
        """
        print("Data channel is created")

        @channel.on("message")
        async def on_message(message):
            response_json = json.loads(message)
            frame_no = response_json['frame_no']
            display_error(ballTrack.original_coords[frame_no], (response_json['x'], response_json['y']))

    def add_tracks():
        """Add video tracks to the RTCPeerConnection."""
        pc.addTrack(ballTrack)

    # connect signaling
    await signaling.connect()

    # creating data channel
    channel = pc.createDataChannel("chat")

    @channel.on("open")
    def on_open():
        """Handle the opening of the data channel."""
        print("Channel is open")

    # send offer
    add_tracks()
    await pc.setLocalDescription(await pc.createOffer())
    await signaling.send(pc.localDescription)

    # consume signaling
    while True:
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)

            if obj.type == "offer":
                # send answer
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)

        elif obj is BYE:
            print("Exiting")
            break

if __name__ == "__main__":
    print("Starting server")
    parser = argparse.ArgumentParser()
    add_signaling_arguments(parser)
    args = parser.parse_args(["-s", "tcp-socket", "--signaling-host", os.environ.get("HOSTNAME", "127.0.0.1"), 
                              "--signaling-port", os.environ.get("PORT", "1234")])

    signaling = create_signaling(args)
    pc = RTCPeerConnection()

    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            run(
                pc=pc,
                signaling=signaling,
            )
        )
    except KeyboardInterrupt:
        pass
    finally:
        # cleanup
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())
