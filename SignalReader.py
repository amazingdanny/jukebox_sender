import RPi.GPIO as GPIO
import time
import threading

class SignalReader:
    def __init__(self, pin: int, pattern_idle_timeout_us: int = 800_000):
        self.pin = pin
        self.pattern_idle_timeout_us = pattern_idle_timeout_us
        self.pattern = []
        self.last_tick_ns = 0
        self.last_level = 0
        self.lock = threading.Lock()
        self.running = False
        self.debug_time = 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def start(self):
        self.running = True
        self.debug_time = 0
        self.last_tick_ns = 0
        self.last_level = 0
        GPIO.add_event_detect(self.pin, GPIO.BOTH, callback=self._edge_detected)

    def stop(self):
        self.running = False
        GPIO.remove_event_detect(self.pin)

    def _edge_detected(self, channel):
        if not self.running:
            return

        level = GPIO.input(self.pin)
        current_tick_ns = time.time_ns()

        if self.last_tick_ns == 0:
            # First edge, just initialize
            if level == 1:
                self.debug_time = time.time_ns()
                self.last_tick_ns = current_tick_ns
                self.last_level = level
            return

        # Duration in microseconds since last edge
        duration = (current_tick_ns - self.last_tick_ns) // 1000
        with self.lock:
            self.pattern.append(duration)

        self.last_tick_ns = current_tick_ns
        self.last_level = level

    def get_pattern(self):
        if not self.pattern:
            return []

        current_tick_ns = time.time_ns()
        idle_us = (current_tick_ns - self.last_tick_ns) // 1000
        end_time = time.time_ns()
        if (idle_us >= self.pattern_idle_timeout_us and self.last_level == 0) or end_time - self.debug_time > 3_400_000_000 :
            with self.lock:
                print(f"Pattern captured in {(end_time - self.debug_time):.3f} seconds")
                pattern = self.pattern[:]
                self.pattern.clear()
                self.last_tick_ns = 0
                self.last_level = 0
                self.debug_time = time.time_ns()
            return pattern

        return []
