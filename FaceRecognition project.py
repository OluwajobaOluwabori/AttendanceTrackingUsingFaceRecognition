import mysql.connector
import face_recognition  # Library for face recognition
import os  # Library to handle file paths and directories
import numpy as np  # Library for numerical operations
import cv2  # OpenCV library for image processing
import base64

#Connecting to MySQL Database
db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='Ass3')  

cursor = db.cursor() #Cursor to execute SQL queries

# Function to Process and Save Known Face Encodings in the database
def ProcessandSaveEncodings():
    dir = 'C:\\Users\\Etudiant FST\\OneDrive - UPEC\\SoftwareIntegration\\Session 2 - Face Recognition + Mediapipe\\images'  # Get the working directory
    
    
    faces = [f for f in os.listdir(dir) if f.lower().endswith(('.jpg', '.png'))]  # Get all image files (JPG, PNG) in the directory
    images_known = []  # List to store image file paths
    
    # Create full paths for each image file
    for x in faces:
        images_known.append(dir + "/" + x)

    known_face_encodings = []  # List to store face encodings
    known_face_names = []  # List to store corresponding names

    # Process each image to extract face encodings
    for x in images_known:
        known_image = face_recognition.load_image_file(x)  # Load image
        known_face_encoding = face_recognition.face_encodings(known_image, model="small")[0]  # Extract face encoding
        known_face_encodings.append(known_face_encoding)  # Store encoding
        known_face_names.append(os.path.basename(x))  # Store filename (used as name)

    print(known_face_encodings) # Debug: Print known face encodings
    print("Original Length:", len(known_face_encodings[0])) # Debug: Print length of encodings

    # Save encodings in database
    for name, encoding in zip(known_face_names,known_face_encodings):
        name = os.path.splitext(name)[0] # Remove file extension
        query = 'INSERT INTO known_faces (name, encoding, timestamp) VALUES (%s, %s, CURRENT_TIMESTAMP())'
        cursor.execute(query, (name, base64.b64encode(encoding.tobytes()).decode('utf-8')))   # Convert encoding to Base64
        db.commit()
    # return known_face_encodings, known_face_names  # Return face encodings and names but not needed 


# Function for Face Recognition Using Webcam

def WebcamFaceRecognition():
    video_capture = cv2.VideoCapture(0)  # Open webcam (0 = default camera)
    # known_face_encodings, known_face_names = ProcessandSaveEncodings()  # Load known faces

    while True:
        ret, frame = video_capture.read()  # Read a frame from the webcam
        face_locations = face_recognition.face_locations(frame, model='hog') # Detect faces in the frame
        face_encodings = face_recognition.face_encodings(frame, face_locations,model='small')  # Extract encodings
        # print(face_encodings) # Debug: Print encodings of faces in the webcam feed

        # Retrieve stored face encodings from the database
        encoding_query = 'SELECT encoding FROM known_faces'
        cursor.execute(encoding_query)   
        encoded_face_encodings = cursor.fetchall()

        # Convert Base64-encoded encodings back to NumPy arrays
        known_face_encodings = [np.frombuffer(base64.b64decode(encoding), dtype=np.float64, count= -1) for list in encoded_face_encodings for encoding in list]

        print("Decoded Length:", len(known_face_encodings[0])) # Debug: Check the new encoding size, should be the same with the original

        # Load Names of Known Faces
        name_query = 'SELECT name FROM known_faces'
        cursor.execute(name_query)   
        known_face_names = cursor.fetchall()
        known_face_names = [names for list in known_face_names for names in list]
        # print(known_face_names)  Debug: Print names saved in the dataase
    
        # Face Matching & Logging
        # Iterate through detected faces and compare with known faces
        for (top,right,bottom,left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings,face_encoding) # Compare with known faces
            print(matches)
            name = "Unknown"  # Default name

            # Compute distances and find best match
            face_distances = face_recognition.face_distance(known_face_encodings,face_encoding)
            best_match_index = np.argmin(face_distances)   # Find the closest match


            if matches[best_match_index]: # If a match is found, get name
                name = known_face_names[best_match_index]
                name = os.path.splitext(name)[0] # Remove file extension

                # Check if the person was detected in the last 12 hours
                query_check = 'SELECT COUNT(*) FROM detected_faces WHERE detected_name = %s AND TIMESTAMPDIFF(HOUR, NOW(), timestamp) < 12'
                cursor.execute(query_check,(name,))
                result = cursor.fetchone()

                if result[0] == 0:  # If not detected in the last 12 hours, insert into database
                    query = 'INSERT INTO detected_faces (detected_name, timestamp) VALUES (%s, CURRENT_TIMESTAMP())'
                    cursor.execute(query, (os.path.splitext(name)[0],))   
                    db.commit()
                    print(f"Logged {name} into database.")
                else:
                    print(f"{name} was already logged within the last 12 hours. Skipping entry.")

                # Draw a rectangle around the detected face
                # Parameters: (image, top-left corner, bottom-right corner, color (BGR), thickness)
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                # Draw a filled rectangle below the face for labeling
                # Parameters: (image, top-left of label, bottom-right of label, color (BGR), fill the rectangle)
                cv2.rectangle(frame, (left, bottom - 25), (right, bottom), (0, 0, 255), cv2.FILLED)

                # Write the detected name on the video frame
                # Parameters: (image, text, start position, font type, font scale, color (BGR), thickness)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 4, bottom - 4), font, 1, (255, 255, 255), 1)

        # Display the processed video frame
        cv2.imshow('Video', frame)

        # Break the loop if 'esc' is pressed
        if cv2.waitKey(1) & 0xFF == 27:
            break

    # Release webcam and close OpenCV windows
    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    # ProcessandSaveEncodings()
    WebcamFaceRecognition()
