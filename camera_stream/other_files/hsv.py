# hsv working on laptop camera with contour and middle point

import cv2
import numpy as np

# Function to detect red and green colors in a frame
def detect_colors(frame):
    # Convert the frame from BGR to HSV color space
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define the lower and higher HSV values for the red color
    lower_red = np.array([0, 100, 100])
    upper_red = np.array([10, 255, 255])
    lower_red_wrap = np.array([170, 100, 100])
    upper_red_wrap = np.array([180, 255, 255])

    # Define the lower and higher HSV values for the green color
    lower_green = np.array([40, 100, 100])
    upper_green = np.array([80, 255, 255])

    # Create masks for red and green colors
    mask_red1 = cv2.inRange(hsv_frame, lower_red, upper_red)
    mask_red2 = cv2.inRange(hsv_frame, lower_red_wrap, upper_red_wrap)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)
    mask_green = cv2.inRange(hsv_frame, lower_green, upper_green)

    # Combine both masks
    mask = cv2.bitwise_or(mask_red, mask_green)

    # Find contours in the combined mask image
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Draw contours and add a point to the center of each contour
    for contour in contours:
        # Draw contours on the frame
        cv2.drawContours(frame, [contour], -1, (0, 255, 0), 2)

        # Calculate the center of the contour
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            # Add a point to the center of the contour
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

    return frame

# Capture video from the camera
cap = cv2.VideoCapture(0)

while True:
    # Read a frame from the camera
    ret, frame = cap.read()
    if not ret:
        break

    # Detect colors, draw contours, and add points to the centers
    frame_with_contours = detect_colors(frame)

    # Display the frame with contours and points
    cv2.imshow("Color Detection", frame_with_contours)

    # Check for key press and break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture object and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()
