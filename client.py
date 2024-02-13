import os
import argparse
import asyncio
import cv2
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
)
from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling
import multiprocessing
import json


def get_ball_coordinates(shared_queue, shared_x, shared_y, shared_frame_no, lock, exit_flag):
    """
    Function to detect ball coordinates in each frame and update shared variables.

    Args:
        shared_queue (multiprocessing.Queue): Shared queue to store frame information.
        shared_x (multiprocessing.Value): Shared variable for the x-coordinate of the ball.
        shared_y (multiprocessing.Value): Shared variable for the y-coordinate of the ball.
        shared_frame_no (multiprocessing.Value): Shared variable for the frame number.
        lock (multiprocessing.Lock): Lock for ensuring thread-safe access to shared variables.
        exit_flag (multiprocessing.Event): Event to signal the exit of the function.
    """
    while not exit_flag.is_set():
        frame_no, frame = shared_queue.get()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (11, 11), 0)

        # Apply the HoughCircles method to detect circles in the image
        ball = cv2.HoughCircles(
            blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=50, param1=100, param2=30,
            minRadius=15, maxRadius=25
        )
        if ball is not None:
            x, y, r = ball[0][0]
            with lock:
                shared_x.value = x
                shared_y.value = y
                shared_frame_no.value = frame_no


def display_frame(frame):
    """
    Display the frame using OpenCV.

    Args:
        frame: Frame to be displayed.
    """
    cv2.imshow('frame', frame)
    cv2.waitKey(30)


async def run(pc, signaling, shared_queue, shared_x, shared_y, shared_frame_no, lock):
    """
    Main function to run the WebRTC connection and handle data channels.

    Args:
        pc (RTCPeerConnection): WebRTC PeerConnection instance.
        signaling: Signaling instance for communication.
        shared_queue (multiprocessing.Queue): Shared queue to store frame information.
        shared_x (multiprocessing.Value): Shared variable for the x-coordinate of the ball.
        shared_y (multiprocessing.Value): Shared variable for the y-coordinate of the ball.
        shared_frame_no (multiprocessing.Value): Shared variable for the frame number.
        lock (multiprocessing.Lock): Lock for ensuring thread-safe access to shared variables.
    """
    @pc.on("datachannel")
    async def on_datachannel(channel):
        print("Data channel is created")

        @channel.on("message")
        async def on_message(message):
            print(message)

    @pc.on("track")
    async def on_track(track):
        print("Receiving %s" % track.kind)

        while True:
            try:
                frame = await track.recv()
                frame_no = frame.pts
                frame = frame.to_ndarray(format='bgr24')
                shared_queue.put((frame_no, frame))
                display_frame(frame)
            except Exception as e:
                print(e)

    # connect signaling
    await signaling.connect()

    # creating data channel
    channel = pc.createDataChannel("chat")

    async def send_pings():
        while True:
            with lock:
                x = shared_x.value
                y = shared_y.value
                frame_no = shared_frame_no.value
            if frame_no == -1:
                await asyncio.sleep(1)
                continue
            coord = {"frame_no": frame_no, "x": x, "y": y}
            channel.send(json.dumps(coord))
            await asyncio.sleep(1)

    @channel.on("open")
    def on_open():
        print("Channel is open")
        asyncio.ensure_future(send_pings())

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
    parser = argparse.ArgumentParser()
    add_signaling_arguments(parser)
    args = parser.parse_args(["-s", "tcp-socket", "--signaling-host", os.environ.get("SERVER_HOST", "127.0.0.1"), 
                              "--signaling-port", os.environ.get("SERVER_PORT", "1234")])

    signaling = create_signaling(args)
    pc = RTCPeerConnection()

    exit_flag = multiprocessing.Event()
    shared_queue = multiprocessing.Queue()
    shared_x = multiprocessing.Value('d', 0.0)
    shared_y = multiprocessing.Value('d', 0.0)
    shared_frame_no = multiprocessing.Value('i', -1)
    lock = multiprocessing.Lock()
    process_a = multiprocessing.Process(target=get_ball_coordinates, args=(shared_queue, shared_x, shared_y, shared_frame_no, lock, exit_flag,))
    process_a.start()

    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            run(
                pc=pc,
                signaling=signaling,
                shared_queue=shared_queue,
                shared_x=shared_x,
                shared_y=shared_y,
                shared_frame_no=shared_frame_no,
                lock=lock,         
            )
        )
    except KeyboardInterrupt:
        pass
    finally:
        # cleanup
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())
        exit_flag.set()
        process_a.join()
