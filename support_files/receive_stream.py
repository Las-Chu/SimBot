from flask import Flask, Response, render_template, request, jsonify
import requests
import apriltag
import cv2
import numpy as np
from threading import Lock
import socket

# Create the Flask app

app2 = Flask(__name__)

# Create an AprilTag detector
options = apriltag.DetectorOptions(families="tag36h11")
detector = apriltag.Detector(options, searchpath=apriltag._get_dll_path())

# Lock for thread-safe access to shared variables
tags_lock = Lock()

# Detected tags and tracking tag
detected_tags = []
tracking_tag = None
# double_tracking_tag = None

# Camera parameters - Raspberry Pi Cam V2
focal_length_x = 547.7837  
focal_length_y = 547.8070
principal_point_x = 303.9048  
principal_point_y = 243.7748

glob_url = "192.168.1.3" ### TODO: UPDATE WITH MBOT IP ###

tag_height_meters = 0.065 # TODO: make sure to change for specific april tag 

@app2.route('/april_tag_double_click', methods=['POST'])
def april_tag_double_click():
    global tracking_tag
    # global double_tracking_tag
    with tags_lock:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid data'}), 400

        x, y = data.get('x'), data.get('y')

        # Find the tag that encapsulates the x, y coordinates.
        for tag in detected_tags:
            if x >= tag['xMin'] and x <= tag['xMax'] and y >= tag['yMin'] and y <= tag['yMax']:
                # send_double_click_data(tag)  # Call the function to send the data
                # double_tracking_tag = tag
                distance, angle = get_distance_and_angle(tag['pose'])
                send_double_click_data(angle, distance, tag['id'])
                return jsonify({'message': 'Double-click on AprilTag detected and data sent.'})
        
        return jsonify({'message': 'Double-clicked outside all tags'})

@app2.route('/april_tag_click', methods=['POST'])
def april_tag_click():
    global tracking_tag
    # global double_tracking_tag
    with tags_lock:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid data'}), 400

        x, y = data.get('x'), data.get('y')

        for tag in detected_tags:
            if x >= tag['xMin'] and x <= tag['xMax'] and y >= tag['yMin'] and y <= tag['yMax']:
                tracking_tag = tag
                #
                return jsonify({'message': 'Switched to tag centering mode.'})
        
        return jsonify({'message': 'Clicked outside of all tags'})

@app2.route('/')
def index():
    return render_template('index.html')

@app2.route('/video')
def video():
    return Response(get_frames(), mimetype='multipart/x-mixed-replace;boundary=frame')

def get_frames():
    url = f'http://{glob_url}:5000/video_feed'
    response = requests.get(url, stream=True)

    frame_buffer = b''

    for chunk in response.iter_content(chunk_size=1024):
        frame_buffer += chunk
        frame_end = frame_buffer.find(b'\xff\xd9')  
        while frame_end != -1:
            frame_start = frame_buffer.find(b'\xff\xd8')  
            if frame_start != -1:
                frame = frame_buffer[frame_start:frame_end + 2]

                processed_frame = process_frame(frame)

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + processed_frame + b'\r\n')

                frame_buffer = frame_buffer[frame_end + 2:]

            frame_end = frame_buffer.find(b'\xff\xd9')
def process_frame(frame):
    global detected_tags  
    global tracking_tag  
    # global double_tracking_tag

    nparr = np.frombuffer(frame, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # results = detector.detect(gray)

    results, overlay = apriltag.detect_tags(gray,
                                            detector,
                                            camera_params=(focal_length_x, focal_length_y, principal_point_x, principal_point_y),
                                            tag_size=tag_height_meters,
                                            vizualization=3,
                                            verbose=3,
                                            annotation=True
                                              )

    with tags_lock:    
        if tracking_tag is None:
            detected_tags.clear()
            i = 0
            while (i < len(results)):
                (ptA, ptB, ptC, ptD)  = results[i].corners
                corners = results[i].corners
                corners = np.array(results[i].corners, dtype=np.int32)
                cv2.polylines(image, [corners], True, (0, 255, 0), 2)
                ptB = (int(ptB[0]), int(ptB[1]))
                ptC = (int(ptC[0]), int(ptC[1]))
                ptD = (int(ptD[0]), int(ptD[1]))
                ptA = (int(ptA[0]), int(ptA[1]))

                cX = int(results[i].center[0])
                cY = int(results[i].center[1])
                distance, angle = get_distance_and_angle(results[i + 1])
                
                tag = {
                    'xMin': int(corners[:, 0].min()),
                    'yMin': int(corners[:, 1].min()),
                    'xMax': int(corners[:, 0].max()),
                    'yMax': int(corners[:, 1].max()),
                    'id' : results[i].tag_id,
                    'pose': results[i + 1],
                    'center': results[i].center
                    
                }
                detected_tags.append(tag)
                i+=4
        else:
            if tracking_tag is not None:
                print("============ IN SINGLE TRACKING TAG =========== ")
                # Handle tracking mode
                i = 0
                cur_tag_detected = False 
                while (i < len(results)):
                    
                    corners = np.array(results[i].corners, dtype=np.int32)
                    if tracking_tag['id'] == results[i].tag_id:  # Assuming each tag has a unique 'id'
                        cur_tag_detected = True
                        cv2.polylines(image, [corners], True, (0, 0, 255), 2)
                        # distance = calculate_distance(corners)
                        distance, angle = get_distance_and_angle(results[i + 1])
                        tracking_tag['corners'] = corners
                        send_tag_data_to_remote_two(angle, distance, results[i + 1])
                        if distance < 0.1:
                            # tag_meet_distance = True
                            send_message('DISTANCE MET')
                        # Send head-on data
                        if is_tag_head_on(angle):
                            # tag_is_head_on = True
                            send_message('HEAD ON MET')
                        if distance < 0.1 and is_tag_head_on(angle): ### TODO: TUNE ME ###
                            tracking_tag = None
                            # double_tracking_tag = None
                            print("DONE TRACKING TAG")
                            send_tag_done_to_remote(distance)

                        else:
                            send_tag_data_to_remote(tracking_tag, distance, angle)
                        break
                
                # If the tag is not detected, send a message
                if (cur_tag_detected == False):
                    send_message("Out of Sight")
                    tracking_tag = None
            # else:
            #     # double tracking tag 
            #     print("============ IN DOUBLE TRACKING TAG =========== ")
            #     i = 0
            #     cur_tag_detected = False 
            #     while (i < len(results)):
            #         corners = np.array(results[i].corners, dtype=np.int32)
            #         if double_tracking_tag['id'] == results[i].tag_id:  # Assuming each tag has a unique 'id'
            #             cur_tag_detected = True
            #             cv2.polylines(image, [corners], True, (255, 0, 0), 2)
            #             # distance = calculate_distance(corners)
            #             distance, angle = get_distance_and_angle(results[i + 1])
            #             double_tracking_tag['corners'] = corners
            #             send_double_click_data(angle, distance, results[i].tag_id)
                        
            #             if is_tag_head_on(angle): ### TODO: TUNE ME ###
            #                 send_tag_done_to_remote_double(distance, double_tracking_tag['id'])
            #                 tracking_tag = None
            #                 double_tracking_tag = None  # Stop tracking
            #                 print("DONE ALIGNING TAG")
                            

            #             # else:
            #             #     send_double_click_data(double_tracking_tag)
            #             break
            #     # If the tag is not detected, send a message
            #     if (not cur_tag_detected):
            #         send_message("Out of Sight")
                
    _, buffer = cv2.imencode('.jpg', image)
    return buffer.tobytes()

def calculate_distance(corners):
    y_min, y_max = corners[:, 1].min(), corners[:, 1].max()
    distance = -1 * (tag_height_meters * focal_length_y) / (y_min - y_max)
    return distance

def send_tag_data_to_remote_two(angle, distance, pose):
    print("sending info...")
    head_on = False
    if (is_tag_head_on(angle)):
        head_on = True
    data = {
        'angle': angle,
        'distance': distance,
    }
    remote_url = f'http://{glob_url}:5003'
    try:
        # Send the data to the remote server
        requests.post(remote_url, json=data)

    except requests.RequestException as e:
        print(f"Error sending tag data to remote: {e}")

def yaw_angle(R):

    # Extract Translational Matrix
    t_vec = R[:3, 3]

    # Grab Angle from x - z
    angle = np.arctan2(t_vec[0], t_vec[2])
    return np.degrees(angle)

def get_distance_and_angle(pose_matrix):

    # Calculate the Yaw angle
    translation_vector = np.linalg.norm(pose_matrix[0:3, 3])
    angle = yaw_angle(pose_matrix)
    
    # Calculate the distance
    distance = np.linalg.norm(translation_vector)

    return distance, angle


def is_tag_head_on(angle):

    # Compute each corner's angle and check if they are within the tolerance
    tolerance = 10  # degrees
    expected_angle = 0  # degrees

    if not (expected_angle - tolerance <= angle <= expected_angle + tolerance):
        return False

    # If we reach here, all angles are within tolerance. The tag is considered head-on.
    return True


def send_message(message):
    print("sending info...")
    data = {
        'status': message
    }
    remote_url = f'http://{glob_url}:5003'
    try:
        requests.post(remote_url, json=data)
    except requests.RequestException as e:
        print(f"Error sending done message to remote: {e}")


def send_tag_data_to_remote(tag, distance, angle):
    # You were passing corners and distance which would not be available here. 
    # We need to fetch or calculate them within this function now.
    print("sending info...")
    # corners = tag['corners']  # Assuming the 'corners' are stored in the tag dictionary
    head_on = False
    if (is_tag_head_on(angle)):
        head_on = True

    data = {
        'angle': angle,
        'distance': distance,
    }
    remote_url = f'http://{glob_url}:5003'

    try:
        requests.post(remote_url, json=data)
    except requests.RequestException as e:
        print(f"Error sending tag data to remote: {e}")

def send_tag_done_to_remote(distance):
    print("sending info...")
    data = {
        'status': 'DONE',
        'distance': distance
    }
    remote_url = f'http://{glob_url}:5003'
    try:
        requests.post(remote_url, json=data)
    except requests.RequestException as e:
        print(f"Error sending done message to remote: {e}")

def send_tag_done_to_remote_double(distance, id):
    print("sending info double...")
    data = {
        'status': 'DONE DOUBLE',
        'distance': distance,
        'id': id
    }
    remote_url = f'http://{glob_url}:5003'
    try:
        requests.post(remote_url, json=data)
    except requests.RequestException as e:
        print(f"Error sending done message to remote: {e}")


def send_double_click_data(angle, distance, tag_id):
    remote_url = f'http://{glob_url}:5003'
    # distance, angle = get_distance_and_angle(tag['pose'])  # Assumes pose contains the pose matrix
    
    data = {
        'distance': distance,
        'id': tag_id,
        'angle': angle,
        'log': 'Log',
    }
    
    try:
        # Send the data to the remote server once
        requests.post(remote_url, json=data)
    except requests.RequestException as e:
        print(f"Error sending double-click data to remote: {e}")

if __name__ == '__main__':
    hostname = socket.gethostname()
    IP = socket.gethostbyname(hostname)
    app2.run(host=IP, port=5005, threaded=True)