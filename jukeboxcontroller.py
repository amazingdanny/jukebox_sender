from PatternDecoder import PatternDecoder
from RaspberrySender import RaspberrySender
from SignalReader import SignalReader
from audiocontroller import AudioController
import time
import os
MUSIC_FOLDER = "/media/daniel/0103-FBB9"

class JukeboxController:
    def __init__(self, pin: int, receiver_ip: str, receiver_port: int, known_patterns: dict):
        self.reader = SignalReader(pin)
        self.decoder = PatternDecoder(known_patterns)
        self.sender = RaspberrySender(receiver_ip, receiver_port)
        self.folder_path = MUSIC_FOLDER
        self.audio_controller = AudioController(MUSIC_FOLDER, None)
        self.is_bluetooth = False

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
                if decoded :
                    print(f"Decoded selection: {decoded}")
                    if decoded == "K9":
                        if os.path.exists(self.folder_path):
                            #print("Switching Bluetooth mode")
                            if self.is_bluetooth:
                                print("Stopping Bluetooth mode")
                                self.audio_controller.stop()
                                self.is_bluetooth = False
                            elif not self.is_bluetooth:
                                print("Starting Bluetooth mode")
                                self.sender.send("K8")
                                self.is_bluetooth = True

                    if self.is_bluetooth:
                        if decoded == 'K1':
                            self.audio_controller.skip()
                        elif decoded == 'K2':
                            self.audio_controller.pause()
                        elif decoded == 'K3':
                            self.audio_controller.resume()
                        elif decoded == 'K4':
                            self.audio_controller.clear_queue()
                        elif decoded == 'K5':
                            self.audio_controller.queue_random_song()
                        elif decoded == 'K6':
                            self.audio_controller.play_10_random_songs()
                        else:
                            matching_files = self.find_matching_files(decoded)
                            if matching_files:
                                print(f"Found matching files: {matching_files}")
                                file_to_play = matching_files[0]
                                full_path = os.path.join(self.folder_path, file_to_play)
                                if os.path.isfile(full_path):
                                    self.audio_controller.play(full_path, file_to_play, self.is_bluetooth)
                                elif os.path.isdir(full_path):
                                    self.audio_controller.queue_folder(full_path, self.is_bluetooth)
                                print(f"Playing file: {file_to_play}")
                    else:
                        self.sender.send(decoded)
                else:
                    print(f"Unknown pattern: {pattern}")

        except KeyboardInterrupt:
            print("Stopping controller.")
        finally:
            self.reader.stop()
            print("Controller stopped.")


    def find_matching_files(self, pattern: str):
        matching_files = []
        if not os.path.exists(self.folder_path):
            return matching_files
        for filename in os.listdir(self.folder_path):
            file_path = os.path.join(self.folder_path, filename)
            try:
                if filename.startswith(pattern):
                    matching_files.append(filename)
            except Exception:
                continue
        return matching_files
