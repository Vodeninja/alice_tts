# Alice TTS Generator | Генератор речи Alice

[English](#english) | [Русский](#russian)

<a name="english"></a>
# English

Text-to-speech generator based on Yandex Alice TTS with customizable playback parameters.

## Features

- Text-to-speech generation
- Voice selection (shitova.us)
- Playback parameter customization:
  - Volume
  - Bass boost
  - Speed
  - Gain
- Output device selection
- Settings persistence
- Large text support
- Text context menu

## Requirements

- Python 3.8+
- FFmpeg
- Dependencies from requirements.txt

## Installation

1. Install FFmpeg:
   - Windows: Download from [official website](https://ffmpeg.org/download.html)
   - Linux: `sudo apt install ffmpeg`
   - macOS: `brew install ffmpeg`

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the program:
```bash
python main.py
```

2. Enter text in the input field

3. Select parameters:
   - Voice
   - Output device
   - Volume (0-100%)
   - Bass boost (0-200%)
   - Speed (50-200%)
   - Gain (100-300%)

4. Click "Generate" to create and play speech

5. Use "Stop" to interrupt playback

6. Click "Save Settings" to save current parameters

## Hotkeys

- Ctrl+V - Paste text
- Right mouse button - Context menu

## Notes

- Program automatically splits large texts into parts
- Settings are saved to tts_config.json
- Temporary files are automatically deleted after use

---

<a name="russian"></a>
# Русский

Генератор речи на основе Yandex Alice TTS с возможностью настройки параметров воспроизведения.

## Возможности

- Генерация речи из текста
- Выбор голоса (shitova.us)
- Настройка параметров воспроизведения:
  - Громкость
  - Басс буст
  - Скорость
  - Усиление
- Выбор устройства вывода
- Сохранение настроек
- Поддержка больших текстов
- Контекстное меню для работы с текстом

## Требования

- Python 3.8+
- FFmpeg
- Зависимости из requirements.txt

## Установка

1. Установите FFmpeg:
   - Windows: Скачайте с [официального сайта](https://ffmpeg.org/download.html)
   - Linux: `sudo apt install ffmpeg`
   - macOS: `brew install ffmpeg`

2. Установите зависимости Python:
```bash
pip install -r requirements.txt
```

## Использование

1. Запустите программу:
```bash
python main.py
```

2. Введите текст в поле ввода

3. Выберите параметры:
   - Голос
   - Устройство вывода
   - Громкость (0-100%)
   - Басс буст (0-200%)
   - Скорость (50-200%)
   - Усиление (100-300%)

4. Нажмите "Сгенерировать" для создания и воспроизведения речи

5. Используйте "Остановить" для прерывания воспроизведения

6. Нажмите "Сохранить настройки" для сохранения текущих параметров

## Горячие клавиши

- Ctrl+V - Вставить текст
- Правая кнопка мыши - Контекстное меню

## Примечания

- Программа автоматически разбивает большие тексты на части
- Настройки сохраняются в файл tts_config.json
- Временные файлы автоматически удаляются после использования 