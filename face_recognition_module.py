import cv2
import numpy as np
from deepface import DeepFace
from config import DEEPFACE_MODEL, DEEPFACE_DETECTOR, FACE_MATCH_THRESHOLD


class FaceRecognitionModule:
    """Face recognition handler using DeepFace"""

    def __init__(self):
        self.model_name = DEEPFACE_MODEL
        self.detector_backend = DEEPFACE_DETECTOR
        self.threshold = FACE_MATCH_THRESHOLD
        self._initialized = False
        self._warm_up_done = False

    def warm_up(self):
        """Warm up the face recognition model on first use"""
        if self._warm_up_done:
            return
        try:
            print("🔄 Warming up face recognition model...")
            # Do a quick dummy operation to load the model
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    # Try to detect a face (will fail but loads the model)
                    try:
                        DeepFace.extract_faces(frame, detector_backend=self.detector_backend, enforce_detection=False)
                    except:
                        pass
                cap.release()
            self._warm_up_done = True
            print("✅ Face recognition model ready")
        except Exception as e:
            print(f"⚠️ Warm-up warning: {e}")

    def capture_face(self, save_path=None):
        """Capture face from webcam"""
        # Ensure warm-up is done
        self.warm_up()
        
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("❌ Cannot open camera")
            return None

        print("📸 Camera opened. Press SPACE to capture or ESC to cancel")

        captured_frame = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)

            # Draw instructions
            cv2.putText(frame, "Press SPACE to capture, ESC to cancel", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Try to detect face
            try:
                face_objs = DeepFace.extract_faces(
                    frame,
                    detector_backend=self.detector_backend,
                    enforce_detection=False
                )

                if face_objs and len(face_objs) > 0:
                    # Draw rectangle around detected face
                    for face_obj in face_objs:
                        facial_area = face_obj['facial_area']
                        x, y, w, h = facial_area['x'], facial_area['y'], facial_area['w'], facial_area['h']
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.putText(frame, "Face Detected", (x, y-10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            except:
                pass

            cv2.imshow('Capture Face', frame)

            key = cv2.waitKey(1) & 0xFF

            if key == 32:  # SPACE key
                captured_frame = frame.copy()
                print("✅ Face captured!")
                break
            elif key == 27:  # ESC key
                print("❌ Capture cancelled")
                break

        cap.release()
        cv2.destroyAllWindows()

        # Save image if path provided
        if captured_frame is not None and save_path:
            cv2.imwrite(save_path, captured_frame)
            print(f"✅ Image saved: {save_path}")

        return captured_frame

    def generate_embedding(self, image):
        """Generate face embedding from image"""
        try:
            # If image is a file path
            if isinstance(image, str):
                embedding_objs = DeepFace.represent(
                    img_path=image,
                    model_name=self.model_name,
                    detector_backend=self.detector_backend,
                    enforce_detection=False
                )
            else:
                # If image is numpy array
                embedding_objs = DeepFace.represent(
                    img_path=image,
                    model_name=self.model_name,
                    detector_backend=self.detector_backend,
                    enforce_detection=False
                )

            if embedding_objs and len(embedding_objs) > 0:
                embedding = embedding_objs[0]['embedding']
                print(f"✅ Embedding generated (dimension: {len(embedding)})")
                return embedding
            else:
                print("❌ No face detected in image")
                return None
        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            return None

    def verify_faces(self, img1, img2):
        """Verify if two faces match"""
        try:
            result = DeepFace.verify(
                img1_path=img1,
                img2_path=img2,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                enforce_detection=False
            )

            distance = result['distance']
            verified = result['verified']

            print(f"Face verification: {'✅ Match' if verified else '❌ No match'} (distance: {distance:.4f})")
            return verified, distance
        except Exception as e:
            print(f"❌ Error verifying faces: {e}")
            return False, 1.0

    def compare_embeddings(self, embedding1, embedding2):
        """Compare two DeepFace embeddings using cosine similarity"""
        try:
            emb1 = np.array(embedding1, dtype=np.float32)
            emb2 = np.array(embedding2, dtype=np.float32)

            # Cosine similarity
            dot = np.dot(emb1, emb2)
            norm1 = np.linalg.norm(emb1)
            norm2 = np.linalg.norm(emb2)
            similarity = dot / (norm1 * norm2 + 1e-6)

            # Convert similarity to distance
            distance = 1 - similarity

            # Use configured threshold
            threshold = getattr(self, "threshold", 0.4)
            is_match = distance < threshold

            # Debug log for visibility
            print(f"[DEBUG] Face match check → Distance: {distance:.4f}, Threshold: {threshold}, Match: {is_match}")

            return is_match, distance

        except Exception as e:
            print(f"❌ Error comparing embeddings: {e}")
            return False, 1.0

    def find_matching_face(self, test_embedding, database_embeddings):
        """Find matching face from database of embeddings"""
        if not database_embeddings:
            print("⚠️ No database embeddings provided")
            return None, float('inf')
            
        best_match = None
        best_distance = float('inf')

        for person_id, stored_embedding in database_embeddings.items():
            is_match, distance = self.compare_embeddings(test_embedding, stored_embedding)

            if is_match and distance < best_distance:
                best_distance = distance
                best_match = person_id

        if best_match:
            print(f"✅ Match found: {best_match} (distance: {best_distance:.4f})")
        else:
            print("❌ No matching face found")

        return best_match, best_distance

    def recognize_face_from_camera(self, database_embeddings, callback=None):
        """Real-time face recognition from camera"""
        # Ensure warm-up
        self.warm_up()
        
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("❌ Cannot open camera")
            return None

        print("📸 Camera opened for recognition. Press ESC to cancel")

        recognized_person = None
        frame_count = 0
        check_interval = 3  # Check every 3 frames for faster recognition

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Flip frame horizontally
            frame = cv2.flip(frame, 1)

            # Draw instructions - No circle constraint
            cv2.putText(frame, "Face Recognition Active - Face anywhere on screen", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, "Press ESC to cancel", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            frame_count += 1

            # Check face every N frames
            if frame_count % check_interval == 0:
                try:
                    # Generate embedding for current frame
                    embedding = self.generate_embedding(frame)

                    if embedding:
                        # Find matching face
                        match_id, distance = self.find_matching_face(embedding, database_embeddings)

                        if match_id:
                            recognized_person = match_id
                            cv2.putText(frame, f"Match: {match_id}", (10, 90), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                            # Call callback if provided
                            if callback:
                                callback(match_id)

                            # Wait a bit before closing
                            cv2.imshow('Face Recognition', frame)
                            cv2.waitKey(1500)
                            break
                except Exception as e:
                    print(f"⚠️ Frame processing error: {e}")

            cv2.imshow('Face Recognition', frame)

            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC key
                print("❌ Recognition cancelled")
                break

        cap.release()
        cv2.destroyAllWindows()

        return recognized_person

    def detect_and_mark_attendance(self, database_students, mark_callback):
        """
        Detect faces and mark attendance in real-time
        Optimized for faster recognition - no circle constraint, face can be anywhere on screen
        database_students: dict with student_id as key and embedding as value
        mark_callback: function to call when face is recognized with student_id
        """
        # Ensure warm-up is done first
        self.warm_up()
        
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("❌ Cannot open camera")
            return

        print("📸 Attendance marking active. Press ESC to stop")
        print("💡 Tip: Face can be anywhere on screen - no need to center in circle")

        marked_students = set()  # Track already marked students
        frame_count = 0
        check_interval = 3  # Check every 3 frames for much faster recognition
        consecutive_no_match = 0
        max_no_match_before_retry = 10

        # Ensure database embeddings are valid
        if not database_students:
            print("❌ No student database available")
            show_toast(None, "No students registered", "error")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)

            # Draw UI - No circle constraint, face can be anywhere on screen
            cv2.putText(frame, "Attendance Marking Active", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, f"Marked: {len(marked_students)} students", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, "Press ESC to stop | Face anywhere on screen", 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            frame_count += 1

            # Check face periodically
            if frame_count % check_interval == 0:
                try:
                    # Generate embedding
                    embedding = self.generate_embedding(frame)

                    if embedding:
                        # Find match
                        match_id, distance = self.find_matching_face(embedding, database_students)

                        if match_id and match_id not in marked_students:
                            # Mark attendance
                            success = mark_callback(match_id)

                            if success:
                                marked_students.add(match_id)
                                print(f"✅ Attendance marked for: {match_id}")
                                consecutive_no_match = 0

                                # Show success message on frame
                                cv2.putText(frame, f"Marked: {match_id}", 
                                           (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                                cv2.imshow('Attendance Marking', frame)
                                cv2.waitKey(800)  # Show for 0.8 seconds - faster feedback
                            else:
                                # Already marked, add to set anyway to skip
                                marked_students.add(match_id)
                                print(f"ℹ️ Already marked: {match_id}")
                        else:
                            consecutive_no_match += 1
                            if consecutive_no_match >= max_no_match_before_retry:
                                print("🔄 Retrying face detection...")
                                consecutive_no_match = 0
                    else:
                        consecutive_no_match += 1
                except Exception as e:
                    print(f"⚠️ Frame processing error: {e}")
                    consecutive_no_match += 1

            cv2.imshow('Attendance Marking', frame)

            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break

        cap.release()
        cv2.destroyAllWindows()

        print(f"✅ Attendance marking completed. Total marked: {len(marked_students)}")
        return len(marked_students)


# Global face recognition instance
face_recognizer = FaceRecognitionModule()
