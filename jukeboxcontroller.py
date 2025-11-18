from PatternDecoder import PatternDecoder
from RaspberrySender import RaspberrySender
from SignalReader import SignalReader
import time

class JukeboxController:
    def __init__(self, pin: int, receiver_ip: str, receiver_port: int, known_patterns: dict):
        self.reader = SignalReader(pin)
        self.decoder = PatternDecoder(known_patterns)
        self.sender = RaspberrySender(receiver_ip, receiver_port)

    def run(self):
        #time.sleep(10)
        print("JukeboxController running... Press Ctrl+C to stop.")
        self.reader.start()

        try:
            while True:
                time.sleep(0.001)  # high resolution for short pulses
                pattern = self.reader.get_pattern()
                if not pattern:
                    continue
                print(f"Read pattern: {pattern}")
                pattern = self.decoder.clean_pattern(pattern)
                decoded = self.decoder.decode(tuple(pattern))
                if decoded:
                    print(f"Decoded selection: {decoded}")
                    self.sender.send(decoded)
                else:
                    print(f"Unknown pattern: {pattern}")

        except KeyboardInterrupt:
            print("Stopping controller.")
        finally:
            self.reader.stop()
            print("Controller stopped.")
