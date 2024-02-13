# WebRTC Bouncing Ball Server & Client

This is a simple WebRTC server that streams video with a bouncing ball using Python and the aiortc library. The server generates a video stream with a bouncing ball, and clients can connect to view the stream and receive the frame of the bouncing ball and returns the coordiante of the ball back to the server where the error from the real coordinates is calculated.

### Requirements
- Python 3.10 or higher
- install requirements from requirements.txt using the following statement
   ```pip install -r requirements.txt```

## Server Code
1. Run the server code using the following command:
    ```python server.py```
2. Clients can connect to the server to view the bouncing ball stream and return the detected cooridinates and the error is calculated on the server.

## Client Code
1. Run the client code using the following command:
    ```python client.py```
2. The client will connect to the server and display the bouncing ball stream and send back the detected coordinates.

### Code Explanation
- The client creates a separate process to detect the coordinates of the bouncing ball in each frame using OpenCV.
- The `run` function sets up the WebRTC connection, handles data channels, and displays the video stream with the bouncing ball.
- Coordinates of the bouncing ball are sent to the server through a data channel, enabling real-time communication.

### Docker Deployment

1. Build the Server Docker
    ```docker build -t bouncing_ball_server -f Dockerfiles/server.Dockerfile .```
2. Build the Client server
    ```docker build -t bouncing_ball_server -f Dockerfiles/client.Dockerfile . ```
3. Create Network
    ```docker network create bouncing_ball_network```
4. Deploying Server Docker
    ```docker run --rm --network=bouncing_ball_network --hostname server-host --name server bouncing_ball_server```
5. Deploying Client Docker
    ```docker run --rm --network=bouncing_ball_network -e SERVER_HOST=server-host -e SERVER_PORT=1234 --name client bouncing_ball_client```

NOTE: The Server port can be changed in the dockerfiles of server and client Dockerfiles in the present in the Dockerfiles folder

### Kubernetes Deployment

1. Start Minikube
    ```minikube start```
2. Configure minikube to use local dockers
    ```eval $(minikube docker-env)``` (in order to access local dockerfiles)
3. Build the Server Docker
    ```docker build -t bouncing_ball_server -f Dockerfiles/server.Dockerfile .```
4. Build the Client Docker
    ```docker build -t bouncing_ball_server -f Dockerfiles/server.Dockerfile .```
5. Deploy Kubernetes Server
    ```kubectl apply -f Kubernetes/server-deployment.yaml```
6. Deploy Kubernetes Client 
    ```kubectl apply -f Kubernetes/client-deployment.yaml```

NOTE: The Server hostname and port can be changed in the kubernetes deployment yaml files of the server and client in the Kubernetes folder