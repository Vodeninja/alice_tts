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

class TTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Alice TTS Generator")
        self.root.geometry("600x550")
        
        self.is_playing = False
        self.devices = sd.query_devices()
        self.output_devices = [d for d in self.devices if d['max_output_channels'] > 0]
        self.volume = 1.0
        self.config_file = "tts_config.json"
        
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(main_frame, text="Введите текст:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.text_input = scrolledtext.ScrolledText(main_frame, width=50, height=10)
        self.text_input.grid(row=1, column=0, columnspan=2, pady=5)
        
        self.setup_text_context_menu()
        
        ttk.Label(main_frame, text="Выберите голос:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.voice_var = tk.StringVar(value="shitova.us")
        voice_combo = ttk.Combobox(main_frame, textvariable=self.voice_var)
        voice_combo['values'] = ('shitova.us', 'alena', 'filipp')
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
        
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        self.generate_btn = ttk.Button(buttons_frame, text="Сгенерировать", command=self.generate_audio)
        self.generate_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(buttons_frame, text="Остановить", command=self.stop_audio, state='disabled')
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        self.save_config_btn = ttk.Button(buttons_frame, text="Сохранить настройки", command=self.save_config)
        self.save_config_btn.grid(row=0, column=2, padx=5)
        
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.grid(row=6, column=0, columnspan=2, pady=5)
        
        self.progress = ttk.Progressbar(main_frame, length=400, mode='indeterminate')
        self.progress.grid(row=7, column=0, columnspan=2, pady=5)
        
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

    def save_config(self):
        config = {
            'volume': self.volume,
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

    def update_volume(self, value):
        self.volume = float(value) / 100.0

    def get_selected_device_id(self):
        if not self.device_var.get():
            return None
        device_name = self.device_var.get().split(" (ID: ")[0]
        for device in self.output_devices:
            if device['name'] == device_name:
                return device['index']
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
            audio_array = (audio_array * self.volume).astype(np.int16)
            device_id = self.get_selected_device_id()
            
            sd.play(audio_array, 48000, device=device_id)
            sd.wait()
            
            self.root.after(0, self._playback_finished)
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"Ошибка воспроизведения: {str(e)}"))
            self.root.after(0, self._playback_finished)
        finally:
            if os.path.exists(temp_ogg):
                os.remove(temp_ogg)

    def _playback_finished(self):
        self.is_playing = False
        self.stop_btn.state(['disabled'])
        self.status_label.config(text="Воспроизведение завершено")

    def stop_audio(self):
        if self.is_playing:
            sd.stop()
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
                        "text": self.text_input.get("1.0", tk.END).strip(),
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
                    self.root.after(0, lambda: self.play_audio(audio_data))
                else:
                    self.root.after(0, lambda: self.status_label.config(text="Аудио не получено"))
                await websocket.close()

def main():
    root = tk.Tk()
    app = TTSApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()