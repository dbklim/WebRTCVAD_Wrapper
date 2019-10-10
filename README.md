# WebRTCVAD Wrapper

Это простая обёртка на Python для [WebRTC](https://webrtc.org/) Voice Activity Detection (VAD). Поддерживается только Python 3.

[VAD](https://en.wikipedia.org/wiki/Voice_activity_detection) - это детектор голосовой активности, который позволяет удалять тишину/извлекать фрагменты с речью (или другими звуками) из wav аудиозаписи.

**WebRTCVAD_Wrapper** упрощает работу с WebRTC VAD: избавляет пользователя от необходимости самому извлекать фреймы/кадры из аудиозаписи и снимает ограничения на параметры обрабатываемой аудиозаписи.

## Установка

Данная обёртка имеет следующие зависимости: [pydub](https://github.com/jiaaro/pydub) и [py-webrtcvad](https://github.com/wiseman/py-webrtcvad).

Установка с помощью pip:
```
pip install git+https://github.com/Desklop/WebRTCVAD_Wrapper
```

## Использование

**1.** Из вашего кода Python (извлечение фрагментов с речью/звуком из `test.wav` и сохранение их как `segment_%i.wav`):
```python
from webrtcvad_wrapper import WebRTCVAD

vad = WebRTCVAD(sensitivity_mode=3)

audio = vad.read_wav('test.wav')
filtered_segments = vad.filter(audio)

segments_with_voice = [filtered_segment[1] for filtered_segment in filtered_segments if filtered_segment[0]]
for j, segment in enumerate(segments_with_voice):
    path = 'segment_%002d.wav' % (j + 1)
    print("Сохранение '%s'" % (path))
    vad.write_wav(path, segment)
```

Класс [WebRTCVAD](https://github.com/Desklop/WebRTCVAD_Wrapper/blob/master/webrtcvad_wrapper/webrtcvad_wrapper.py#L37) содержит следующие методы:
- [`read_wav()`](https://github.com/Desklop/WebRTCVAD_Wrapper/blob/master/webrtcvad_wrapper/webrtcvad_wrapper.py#L208): загрузка .wav аудиозаписи и приведение её в поддерживаемый формат
- [`write_wav()`](https://github.com/Desklop/WebRTCVAD_Wrapper/blob/master/webrtcvad_wrapper/webrtcvad_wrapper.py#L241): сохранение найденных фрагментов в .wav аудиозапись
- [`get_frames()`](https://github.com/Desklop/WebRTCVAD_Wrapper/blob/master/webrtcvad_wrapper/webrtcvad_wrapper.py#L155): извлечение фреймов с необходимым смещением
- [`filter_frames()`](https://github.com/Desklop/WebRTCVAD_Wrapper/blob/master/webrtcvad_wrapper/webrtcvad_wrapper.py#L87): обработка вывода от `webrtcvad.Vad().is_speech()`
- [`filter()`](https://github.com/Desklop/WebRTCVAD_Wrapper/blob/master/webrtcvad_wrapper/webrtcvad_wrapper.py#L66): объединяет `get_frames()` и `filter_frames()`
- [`set_mode()`](https://github.com/Desklop/WebRTCVAD_Wrapper/blob/master/webrtcvad_wrapper/webrtcvad_wrapper.py#L57): установка чувствительности WebRTC VAD

Более подробная информация о поддерживаемых аргументах и работе каждого метода находится в комментариях в исходном коде этих методов.

Особенности:
- WebRTC VAD принимает только PCM 16 бит, моно с частотой дискретизации 8, 16, 32 или 48кГц, по этому метод `read_wav()` автоматически приводит вашу wav аудиозапись в необходимый формат
- WebRTC VAD работает только с фреймами/кадрами длиной 10, 20 или 30 миллисекунд, об этом заботится метод `get_frames()`
- метод `set_mode()` позволяет задать уровень чувствительности (его так же можно задать при создании объекта `WebRTCVAD(0)`), поддерживаются значения от `0` до `3`, где `3` - максимальная чувствительность (по умолчанию используется значение `3`)
- методы `get_frames()`, `filter_frames()` и `filter()` возвращают список из фреймов [`webrtcvad_wrapper.Frame`](https://github.com/Desklop/WebRTCVAD_Wrapper/blob/master/webrtcvad_wrapper/webrtcvad_wrapper.py#L29), которые можно легко конвертировать в байтовою строку (без заголовков .wav, только аудиоданные):
```python
audio = vad.read_wav('test.wav')
filtered_segments = vad.filter(audio)

segments_with_voice = [filtered_segment[1] for filtered_segment in filtered_segments if filtered_segment[0]]
segments_bytes_with_voice = [b''.join([frame.bytes for frame in segment]) for segment in segments_with_voice]
```

---

**2.** В качестве инструмента командной строки:
```
python3 -m webrtcvad_wrapper.cli input.wav output.wav
```
Где:
- `input.wav` - имя исходного .wav аудиозаписи
- `output.wav` или `output` - шаблонное имя для .wav аудиозаписей, в которые будут сохранены найденные фрагменты с речью/звуком в формате `output_%i.wav`

В данном варианте используются следующие параметры:
- WebRTC VAD с уровнем "агрессивности"/чувствительности `3`
- длина фрейма `10` миллисекунд
- фрагмент считается фрагментом с речью/звуком, если он содержит более `90%` фреймов, в которых webrtcvad нашёл речь/звук

---

Если у вас возникнут вопросы или вы хотите сотрудничать, можете написать мне на почту: vladsklim@gmail.com или в [LinkedIn](https://www.linkedin.com/in/vladklim/).