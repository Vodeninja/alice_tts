import asyncio
import websockets
import json
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import sounddevice as sd
import numpy as np
import subprocess
import io
import os
from scipy import signal

class TTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Alice TTS Generator")
        self.root.geometry("600x700")
        
        self.is_playing = False
        self.devices = sd.query_devices()
        self.output_devices = [d for d in self.devices if d['max_output_channels'] > 0]
        self.volume = 1.0
        self.bass_boost = 1.0
        self.speed = 1.0
        self.gain = 1.0
        self.config_file = "tts_config.json"
        self.audio_queue = []
        self.current_audio_index = 0
        self.max_text_length = 1000
        
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(main_frame, text="Введите текст:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.text_input = scrolledtext.ScrolledText(main_frame, width=50, height=10)
        self.text_input.grid(row=1, column=0, columnspan=2, pady=5)
        
        self.setup_text_context_menu()
        
        ttk.Label(main_frame, text="Выберите голос:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.voice_var = tk.StringVar(value="shitova.us")
        voice_combo = ttk.Combobox(main_frame, textvariable=self.voice_var)
        voice_combo['values'] = ('shitova.us')
        voice_combo.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Выберите устройство вывода:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(main_frame, textvariable=self.device_var, width=50)
        self.device_combo['values'] = [f"{d['name']} (ID: {d['index']})" for d in self.output_devices]
        self.device_combo.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Громкость:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.volume_scale = ttk.Scale(main_frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                                    command=self.update_volume)
        self.volume_scale.set(100)
        self.volume_scale.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Басс буст:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.bass_scale = ttk.Scale(main_frame, from_=0, to=200, orient=tk.HORIZONTAL,
                                  command=self.update_bass)
        self.bass_scale.set(100)
        self.bass_scale.grid(row=5, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Скорость:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.speed_scale = ttk.Scale(main_frame, from_=50, to=200, orient=tk.HORIZONTAL,
                                   command=self.update_speed)
        self.speed_scale.set(100)
        self.speed_scale.grid(row=6, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Усиление:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.gain_scale = ttk.Scale(main_frame, from_=100, to=300, orient=tk.HORIZONTAL,
                                  command=self.update_gain)
        self.gain_scale.set(100)
        self.gain_scale.grid(row=7, column=1, sticky=tk.W, pady=5)
        
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=8, column=0, columnspan=2, pady=20)
        
        self.generate_btn = ttk.Button(buttons_frame, text="Сгенерировать", command=self.generate_audio)
        self.generate_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(buttons_frame, text="Остановить", command=self.stop_audio, state='disabled')
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        self.save_config_btn = ttk.Button(buttons_frame, text="Сохранить настройки", command=self.save_config)
        self.save_config_btn.grid(row=0, column=2, padx=5)
        
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.grid(row=9, column=0, columnspan=2, pady=5)
        
        self.progress = ttk.Progressbar(main_frame, length=400, mode='indeterminate')
        self.progress.grid(row=10, column=0, columnspan=2, pady=5)
        
        self.load_config()

    def setup_text_context_menu(self):
        self.context_menu = tk.Menu(self.text_input, tearoff=0)
        self.context_menu.add_command(label="Вставить", command=self.paste_text)
        self.context_menu.add_command(label="Вырезать", command=lambda: self.text_input.event_generate("<<Cut>>"))
        self.context_menu.add_command(label="Копировать", command=lambda: self.text_input.event_generate("<<Copy>>"))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Выделить всё", command=lambda: self.text_input.tag_add(tk.SEL, "1.0", tk.END))
        
        self.text_input.bind("<Button-3>", self.show_context_menu)
        self.text_input.bind("<Control-v>", lambda e: self.paste_text())
        self.text_input.bind("<Control-V>", lambda e: self.paste_text())

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def paste_text(self):
        try:
            text = self.root.clipboard_get()
            self.text_input.insert(tk.INSERT, text)
        except:
            pass

    def update_volume(self, value):
        self.volume = float(value) / 100.0

    def update_bass(self, value):
        self.bass_boost = float(value) / 100.0

    def update_speed(self, value):
        self.speed = float(value) / 100.0

    def update_gain(self, value):
        self.gain = float(value) / 100.0

    def apply_audio_effects(self, audio_array, sample_rate):
        if self.bass_boost != 1.0:
            b, a = signal.butter(4, 0.1, 'low')
            bass = signal.filtfilt(b, a, audio_array)
            audio_array = audio_array + (bass * (self.bass_boost - 1.0))
        
        if self.gain != 1.0:
            audio_array = audio_array * self.gain
        
        max_val = np.max(np.abs(audio_array))
        if max_val > 32767:
            audio_array = audio_array * (32767 / max_val)
        
        return audio_array.astype(np.int16)

    def save_config(self):
        config = {
            'volume': self.volume,
            'bass_boost': self.bass_boost,
            'speed': self.speed,
            'gain': self.gain,
            'voice': self.voice_var.get(),
            'device': self.device_var.get()
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            self.status_label.config(text="Настройки сохранены")
        except Exception as e:
            self.status_label.config(text=f"Ошибка сохранения настроек: {str(e)}")

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                if 'volume' in config:
                    self.volume = config['volume']
                    self.volume_scale.set(self.volume * 100)
                
                if 'bass_boost' in config:
                    self.bass_boost = config['bass_boost']
                    self.bass_scale.set(self.bass_boost * 100)
                
                if 'speed' in config:
                    self.speed = config['speed']
                    self.speed_scale.set(self.speed * 100)
                
                if 'gain' in config:
                    self.gain = config['gain']
                    self.gain_scale.set(self.gain * 100)
                
                if 'voice' in config:
                    self.voice_var.set(config['voice'])
                
                if 'device' in config:
                    device_name = config['device']
                    for i, device in enumerate(self.device_combo['values']):
                        if device_name in device:
                            self.device_combo.current(i)
                            break
        except Exception as e:
            self.status_label.config(text=f"Ошибка загрузки настроек: {str(e)}")

    def get_selected_device_id(self):
        if not self.device_var.get():
            return None
        try:
            device_name = self.device_var.get().split(" (ID: ")[0]
            for device in self.output_devices:
                if device['name'] == device_name:
                    return device['index']
        except:
            return None
        return None

    def play_audio(self, audio_data):
        try:
            if not self.is_playing:
                self.is_playing = True
                self.stop_btn.state(['!disabled'])
                self.status_label.config(text="Воспроизведение...")
                
                thread = threading.Thread(target=self._play_audio_thread, args=(audio_data,))
                thread.daemon = True
                thread.start()
        except Exception as e:
            self.status_label.config(text=f"Ошибка воспроизведения: {str(e)}")
            self.is_playing = False

    def _play_audio_thread(self, audio_data):
        try:
            temp_ogg = "temp.ogg"
            with open(temp_ogg, "wb") as f:
                f.write(audio_data)
            
            process = subprocess.Popen(['ffmpeg', '-i', temp_ogg, '-f', 'wav', '-'], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.DEVNULL)
            
            wav_data = process.stdout.read()
            process.wait()
            
            audio_array = np.frombuffer(wav_data, dtype=np.int16)
            
            if self.speed != 1.0:
                audio_array = signal.resample(audio_array, int(len(audio_array) / self.speed))
            
            audio_array = self.apply_audio_effects(audio_array, 48000)
            
            audio_array = (audio_array * self.volume).astype(np.int16)
            
            device_id = self.get_selected_device_id()
            if device_id is None:
                device_id = sd.default.device[1]
            
            sd.play(audio_array, 48000, device=device_id)
            sd.wait()
            
            self.root.after(0, self._playback_finished)
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"Ошибка воспроизведения: {str(e)}"))
            self.root.after(0, self._playback_finished)
        finally:
            if os.path.exists(temp_ogg):
                os.remove(temp_ogg)

    def split_text(self, text):
        sentences = text.split('. ')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if current_length + len(sentence) > self.max_text_length:
                if current_chunk:
                    chunks.append('. '.join(current_chunk) + '.')
                current_chunk = [sentence]
                current_length = len(sentence)
            else:
                current_chunk.append(sentence)
                current_length += len(sentence)
        
        if current_chunk:
            chunks.append('. '.join(current_chunk) + '.')
        
        return chunks

    def play_next_audio(self):
        if self.current_audio_index < len(self.audio_queue):
            audio_data = self.audio_queue[self.current_audio_index]
            self.current_audio_index += 1
            self.play_audio(audio_data)
        else:
            self.audio_queue = []
            self.current_audio_index = 0
            self._playback_finished()

    def _playback_finished(self):
        self.is_playing = False
        self.stop_btn.state(['disabled'])
        if self.current_audio_index < len(self.audio_queue):
            self.status_label.config(text=f"Воспроизведение части {self.current_audio_index + 1} из {len(self.audio_queue)}")
            self.root.after(100, self.play_next_audio)
        else:
            self.status_label.config(text="Воспроизведение завершено")

    def stop_audio(self):
        if self.is_playing:
            sd.stop()
            self.audio_queue = []
            self.current_audio_index = 0
            self._playback_finished()

    def generate_audio(self):
        self.generate_btn.state(['disabled'])
        self.stop_btn.state(['disabled'])
        self.progress.start()
        self.status_label.config(text="Генерация аудио...")
        
        thread = threading.Thread(target=self.run_tts)
        thread.daemon = True
        thread.start()

    def run_tts(self):
        asyncio.run(self.send_request())
        self.root.after(0, self.update_ui_after_generation)

    def update_ui_after_generation(self):
        self.generate_btn.state(['!disabled'])
        self.progress.stop()
        self.status_label.config(text="Готово!")

    async def send_request(self):
        text = self.text_input.get("1.0", tk.END).strip()
        text_chunks = self.split_text(text)
        self.audio_queue = []
        
        for chunk in text_chunks:
            uri = 'wss://uniproxy.alice.yandex.net/uni.ws'
            
            async with websockets.connect(uri) as websocket:
                request = {
                    "event": {
                        "header": {
                            "messageId": "e9355a7f-6c86-4a49-8c85-2d80532bca90",
                            "name": "Generate",
                            "namespace": "TTS"
                        },
                        "payload": {
                            "emotion": "neutral",
                            "format": "audio/opus",
                            "lang": "ru-RU",
                            "oauth_token": "",
                            "quality": "UltraHigh",
                            "text": chunk,
                            "voice": self.voice_var.get()
                        }
                    }
                }

                await websocket.send(json.dumps(request))

                audio_data = bytearray()
                stream_active = False
                stream_id = None
                audio_received = False

                try:
                    async for message in websocket:
                        if isinstance(message, bytes):
                            audio_data.extend(message)
                            audio_received = True
                            continue
                        
                        try:
                            msg = json.loads(message)
                            if 'directive' in msg:
                                if msg['directive']['header']['name'] == 'Speak':
                                    stream_id = msg['directive']['header'].get('streamId')
                                    stream_active = True

                            elif 'streamcontrol' in msg:
                                if msg['streamcontrol'].get('streamId') == stream_id:
                                    action = msg['streamcontrol'].get('action')
                                    if action == 0:
                                        break

                        except json.JSONDecodeError:
                            continue

                except websockets.exceptions.ConnectionClosed:
                    self.root.after(0, lambda: self.status_label.config(text="Ошибка соединения"))
                
                finally:
                    if audio_data:
                        self.audio_queue.append(audio_data)
                    await websocket.close()

        if self.audio_queue:
            self.root.after(0, lambda: self.play_audio(self.audio_queue[0]))
        else:
            self.root.after(0, lambda: self.status_label.config(text="Аудио не получено"))

def main():
    root = tk.Tk()
    app = TTSApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()