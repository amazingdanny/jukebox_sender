import vlc
import threading
import time
from queue import Queue
from PyQt5.QtCore import QTimer
import os
import random


class AudioController:
    def __init__(self, folder_path : str,  ui_controller=None):
        self.ui_controller = ui_controller
        self.queue = Queue()
        self.queue2 = Queue()
        self.current_song = None
        self.current_file = None
        self.player = vlc.MediaPlayer()
        self.folder_path = folder_path
        self.paused = False

        # Optional: set specific audio output device
        try:
            self.player.audio_output_set("alsa")
            self.player.audio_output_device_set("alsa", "hw:1,0")
            #self.player.audio_output_device_set(None, "hw:1,0")
        except Exception:
            pass

        self.lock = threading.Lock()
        self.skip_flag = threading.Event()
        self.paused_song = None

        # start playback loop in background
        self.thread = threading.Thread(target=self._playback_loop, daemon=True)
        self.thread.start()

    # ----------------------------------------------------------------------
    # Main playback loop
    # ----------------------------------------------------------------------
    def _playback_loop(self):
        while True:
            self.skip_flag.clear()
            filepath = self.queue.get()
            song = self.queue2.get()

            self.current_file = filepath
            self.current_song = song

            # ✅ safe UI updates on main thread
            if self.ui_controller:
                print("yes ui controller")
                #QTimer.singleShot(0, lambda s=song: self.ui_controller.update_song(s))
                self.ui_controller.update_song(self.current_song)
                #self.ui_controller.set_playing_state(True)
                self.ui_controller.update_queue(self.get_current_queue())
            else:
                print("no ui controller")

            # play file
            self._play_file(filepath)
            self._wait_until_finished()
            self.queue.task_done()

            if not self.skip_flag.is_set() and not self.paused:
                self.current_song = "No song playing"

            # ✅ update UI when playback finishes
            if self.ui_controller:
                #self.ui_controller.set_playing_state(False)
                self.ui_controller.update_song(self.current_song)
                QTimer.singleShot(0, lambda: self.ui_controller.update_queue(self.get_current_queue()))

    # ----------------------------------------------------------------------
    # Helper methods
    # ----------------------------------------------------------------------
    def _play_file(self, filepath):
        with self.lock:
            media = vlc.Media(filepath)
            self.player.set_media(media)
            try:
                self.player.audio_output_set("alsa")
                self.player.audio_output_device_set("alsa", "hw:1,0")
                #self.player.audio_output_device_set(None, "hw:1,0")
            except Exception:
                pass
            self.player.play()
            print(f"Playing file: {filepath}")

    def _wait_until_finished(self):
        self.skip_flag.clear()
        started = False

        # wait up to 10s for playback to actually start
        for _ in range(100):
            if self.is_playing():
                started = True
                break
            time.sleep(0.1)
        if not started:
            return

        # update queue periodically while playing
        while self.is_playing() and not self.skip_flag.is_set():
            if self.ui_controller:
                self.ui_controller.update_queue(self.get_current_queue())
            time.sleep(0.2)
        self.player.stop()
        self.skip_flag.clear()

    def get_current_queue(self):
        with self.queue2.mutex:
            queue_list = list(self.queue2.queue)
            if self.current_song and self.current_song in queue_list:
                queue_list.remove(self.current_song)
            return queue_list

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------
    def play(self, filepath, file_to_play):
        self.queue.put(filepath)
        self.queue2.put(file_to_play[:-4])
        #if self.ui_controller:
            #self.ui_controller.update_queue(self.get_current_queue())
        #print(f"Queued filepath: {filepath}")
        print(f"Queued file: {file_to_play[:-4]}")

    def stop(self):
        with self.lock:
            if self.player and self.player.is_playing():
                self.player.stop()
            with self.queue.mutex:
                self.queue.queue.clear()
                self.queue2.queue.clear()
        self.skip_flag.set()

    def pause(self):
        with self.lock:
            if self.player:
                self.paused_song = self.current_song
                try:
                    self.player.pause()
                    self.paused = True
                    if self.ui_controller:
                        self.ui_controller.update_song("Paused: " + self.paused_song)
                except Exception:
                    pass

    def resume(self):
        with self.lock:
            if self.player:
                try:
                    self.paused = False
                    self.player.play()
                    if self.ui_controller:
                        self.ui_controller.update_song(self.paused_song)
                except Exception:
                    pass

    def skip(self):
        self.skip_flag.set()

    def is_playing(self):
        with self.lock:
            try:
                return self.player.is_playing() if self.player else False
            except Exception:
                return False

    def get_current_file(self):
        return self.current_file

    def get_queue_size(self):
        return self.queue.qsize()

    def get_queue_list(self):
        with self.queue.mutex:
            return list(self.queue.queue)

    def clear_queue(self):
        with self.queue.mutex:
            self.queue.queue.clear()
        with self.queue2.mutex:
            self.queue2.queue.clear()
        if self.ui_controller:
            QTimer.singleShot(0, lambda: self.ui_controller.update_queue(self.get_current_queue()))

    import random
    import os

    def queue_random_song(self):
        """Pick a random audio file from the folder and queue it."""
        if not hasattr(self, "folder_path") or not os.path.isdir(self.folder_path):
            print("No valid folder_path set, cannot queue random song.")
            return

        # get all playable files
        all_files = [
            f for f in os.listdir(self.folder_path)
            if os.path.isfile(os.path.join(self.folder_path, f))
               and (f.endswith(".mp3") or f.endswith(".wav") or f.endswith(".flac"))
        ]

        if not all_files:
            print("No audio files found for random play.")
            return

        # pick one random file
        random_file = random.choice(all_files)
        full_path = os.path.join(self.folder_path, random_file)

        # queue it normally
        self.queue.put(full_path)
        self.queue2.put(random_file[:-4])

        print(f"Queued random song: {random_file[:-4]}")

        # optional UI update
        if self.ui_controller:
            QTimer.singleShot(0, lambda: self.ui_controller.update_queue(self.get_current_queue()))

    def play_10_random_songs(self):
        for i in range(10):
            self.queue_random_song()

    def queue_folder(self, folder_path):
        """Queue all audio files from the specified folder."""
        if not os.path.isdir(folder_path):
            print(f"Invalid folder path: {folder_path}")
            return

        # get all playable files
        all_files = [
            f for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f))
               and (f.endswith(".mp3") or f.endswith(".wav") or f.endswith(".flac"))
        ]

        if not all_files:
            print("No audio files found in the specified folder.")
            return

        for file_name in all_files:
            full_path = os.path.join(folder_path, file_name)
            self.queue.put(full_path)
            self.queue2.put(file_name[:-4])
            print(f"Queued file from folder: {file_name[:-4]}")

        # optional UI update
        if self.ui_controller:
            QTimer.singleShot(0, lambda: self.ui_controller.update_queue(self.get_current_queue()))

    def set_volume(self, volume):
        with self.lock:
            if self.player:
                try:
                    self.player.audio_set_volume(int(volume))
                except Exception:
                    pass
