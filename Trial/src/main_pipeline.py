def run(self):
    """Run the main translation loop."""
    self.running = True
    last_update = 0
    last_gesture = None
    last_gesture_time = 0
    last_spoken_time = 0
    gesture_hold_time = 0
    min_gesture_duration = 0.8
    gesture_cooldown = 1.5

    logger.info("Starting ASL translation pipeline...")

    try:
        while self.running:
            current_time = time.time()

            ret, frame = self.cap.read()
            if not ret:
                logger.error("Failed to capture frame")
                break

            if current_time - last_update >= self.config['gesture']['update_interval']:
                gesture, confidence = self.gesture_recognizer.process_frame(frame)
                min_conf = self.config['gesture']['min_confidence']

                if gesture and confidence >= min_conf:
                    if gesture == last_gesture:
                        gesture_hold_time = current_time - last_gesture_time
                    else:
                        last_gesture = gesture
                        last_gesture_time = current_time
                        gesture_hold_time = 0

                    # Update overlay in real-time
                    self.update_overlay(gesture, confidence, speak=False)

                    if (
                        gesture_hold_time >= min_gesture_duration and
                        (current_time - last_spoken_time) >= gesture_cooldown
                    ):
                        logger.info(f"Speaking gesture: {gesture} (Confidence: {confidence:.2f})")
                        self.update_overlay(gesture, confidence, speak=True)
                        last_spoken_time = current_time
                else:
                    # No overlay reset to "no gesture" — skip it!
                    logger.debug("Low confidence or no gesture — skipping update.")

                last_update = current_time

            if self.config.get('debug', {}).get('show_video', False):
                debug_frame = self.gesture_recognizer.draw_landmarks(frame)

                if last_gesture:
                    cv2.putText(
                        debug_frame,
                        f"{last_gesture} ({confidence:.2f})",
                        (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2,
                        cv2.LINE_AA
                    )

                cv2.imshow('ASL Translator', debug_frame)

                if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
                    break

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error in main loop: {e}", exc_info=True)
    finally:
        self.cleanup()
