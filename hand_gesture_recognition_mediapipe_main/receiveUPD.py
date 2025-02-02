import socket

# Raspberry Pi IP address and port
# server_ip = 'localhost'  # Listen on localhost (port forwarding)
server_ip = '192.168.1.3'
server_port = 12345  # Choose a port that is not already in use

# Create a TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the IP address and port
server_socket.bind((server_ip, server_port))

# Listen for incoming connections
server_socket.listen(1)

print("Waiting for a connection...")

# Accept a connection
client_socket, client_address = server_socket.accept()

print("Connected to:", client_address)
try:
    while True:
        # Receive data from the client
        data = client_socket.recv(1024).decode()
        print("Received data:", data)

        # Process the received data: Create variables to split left and right hand
        left_gesture = "Stop"
        right_gesture = "Forward"
        if data == "Continue" or data == "Stop" or data == "SpeedUp" or data == "SlowDown":
            left_gesture = data
        elif data == "Forward" or data == "Backwards" or data == "TurnRight" or data == "TurnLeft":
            right_gesture = data
        else:
            None

        # Process the received data: Write label to file
        # if data == "Continue" or data == "Stop" or data == "SpeedUp" or data == "SlowDown":
        #     with open('left_hand_label.txt', 'w') as f:
        #         f.write(data)
        # elif data == "Forward" or data == "Backwards" or data == "TurnRight" or data == "TurnLeft":
        #     with open('right_hand_label.txt', 'w') as f:
        #         f.write(data)
        # else:
        #     None
        
finally:
    # Close the connection
    client_socket.close()
    server_socket.close()
