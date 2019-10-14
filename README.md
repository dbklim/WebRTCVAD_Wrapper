# WebRTCVAD Wrapper

Это простая обёртка на Python для [WebRTC](https://webrtc.org/) Voice Activity Detection (VAD). Поддерживается только Python 3.

[VAD](https://en.wikipedia.org/wiki/Voice_activity_detection) - это детектор голосовой активности, который позволяет удалять тишину/извлекать фрагменты с речью (или другими звуками) из wav аудиозаписи.

**WebRTCVAD_Wrapper** упрощает работу с WebRTC VAD: избавляет пользователя от необходимости самому извлекать фреймы/кадры из аудиозаписи и снимает ограничения на параметры обрабатываемой аудиозаписи.

Так же он содержит **дополнительный режим работы**, который является отдельным, более **грубым и строгим алгоритмом VAD**, основанным на вычислении мощности звуковой волны (RMS, root-mean-square) и частот пересечения нуля (ZCR, zero-crossing rate). Данный режим будет полезен при подготовке аудиозаписей для обучения нейронной сети, так как он **часто игнорирует вообще всё, кроме гласных и звонких согласных звуков в речи** (или просто громких звуков). Его можно использовать, например, в нейронной сети, предназначенной для:

- классификации пола человека по его речи (gender classification/recognition)
- классификации эмоций человека по его речи (emotion classification/recognition)
- идентификации человека по его голосу (speaker identification/verification)
- классификации аудиозаписей
- разделении голосов (speaker diarization)
- корректировки результатов сведения текста с аудиозаписью (forced alignment)

Однако его нельзя использовать в распознавании речи, потому что данный режим не гарантирует сохранность всех фонем в речи.

## Установка

Данная обёртка имеет следующие зависимости: [pydub](https://github.com/jiaaro/pydub), [librosa](https://github.com/librosa/librosa) и [py-webrtcvad](https://github.com/wiseman/py-webrtcvad).

Установка с помощью pip:
```
pip install git+https://github.com/Desklop/WebRTCVAD_Wrapper
```

## Использование

**1.** Из вашего кода Python (извлечение фрагментов с речью/звуком из `test.wav` и сохранение их как `segment_%i.wav`):
```python
from webrtcvad_wrapper import WebRTCVAD

vad = VAD(sensitivity_level=3)
audio = vad.read_wav('test.wav')
filtered_segments = vad.filter(audio)

segments_with_voice = [[filtered_segment[0], filtered_segment[1]] for filtered_segment in filtered_segments if filtered_segment[-1]]
for i, segment in enumerate(segments_with_voice):
    vad.write_wav('segment_%002d.wav' % (i + 1), audio[segment[0]*1000:segment[1]*1000])
```

Очистка аудиозаписи от тишины (например, для обучения нейронной сети) (извлечение фрагментов с речью/звуком из `test.wav`, объединение их в одну аудиозапись и сохранение как `test_without_silence.wav`):
```python
vad.set_mode(sensitivity_level=4)
audio = vad.read_wav('test.wav')
filtered_segments = vad.filter(audio)

segments_with_voice = [[filtered_segment[0], filtered_segment[1]] for filtered_segment in filtered_segments if filtered_segment[-1]]
audio_without_silence = audio[segments_with_voice[0][0]*1000:segments_with_voice[0][1]*1000]
for segment in segments_with_voice[1:]:
    audio_without_silence += audio[segment[0]*1000:segment[1]*1000]
vad.write_wav('test_without_silence.wav', audio_without_silence)
```

Класс [VAD](https://github.com/Desklop/WebRTCVAD_Wrapper/blob/master/webrtcvad_wrapper/webrtcvad_wrapper.py#L39) содержит следующие методы:
- [`read_wav()`](https://github.com/Desklop/WebRTCVAD_Wrapper/blob/master/webrtcvad_wrapper/webrtcvad_wrapper.py#L373): принимает имя .wav аудиозаписи, приводит её в поддерживаемый формат (см. ниже) и возвращает объект `pydub.AudioSegment` с аудиозаписью
- [`write_wav()`](https://github.com/Desklop/WebRTCVAD_Wrapper/blob/master/webrtcvad_wrapper/webrtcvad_wrapper.py#L394): принимает имя .wav аудиозаписи, объект `pydub.AudioSegment` (или байтовую строку с аудиоданными без заголовков wav) и сохраняет аудиозапись под переданным именем
- [`filter()`](https://github.com/Desklop/WebRTCVAD_Wrapper/blob/master/webrtcvad_wrapper/webrtcvad_wrapper.py#L77): принимает объект `pydub.AudioSegment` (или байтовую строку с аудиоданными без заголовков wav), разбивает аудиозапись на фреймы, фильтрует их по наличию речи/звука (с помощью `webrtcvad.Vad().is_speech()` или дополнительным алгоритмом VAD, в зависимости от заданного уровня чувствительности) и возвращает список из списков с границами сегментов: `[[0.00, 1.23, True/False], ...]` (где `0.00` - начало сегмента (в секундах), `1.23` - конец сегмента, `True/False` - `True`: речь/звук, `False`: тишина)
- [`set_mode()`](https://github.com/Desklop/WebRTCVAD_Wrapper/blob/master/webrtcvad_wrapper/webrtcvad_wrapper.py#L63): принимает целое число от `0` до `4`, которое задаёт уровень чувствительности VAD (значение от `0` до `3` - уровень чувствительности WebRTC VAD, значение `4` - отключение WebRTC VAD и использование дополнительного грубого алгоритма VAD)

Подробная информация о поддерживаемых аргументах и работе каждого метода находится в комментариях в исходном коде этих методов.

Особенности:
- WebRTC VAD принимает только PCM 16 бит, моно, по этому метод `read_wav()` автоматически приводит вашу wav аудиозапись в необходимый формат
- WebRTC VAD работает только с фреймами/кадрами длиной 10, 20 или 30 миллисекунд и частотой дискретизации 8, 16, 32 или 48кГц, об этом заботится метод `filter()`
- метод `set_mode()` позволяет задать уровень чувствительности (его так же можно задать при создании объекта `VAD(0)`), поддерживаются значения от `0` до `4`, где `4` - максимальная чувствительность (по умолчанию используется значение `3`). Значения от `0` до `3` являются базовыми для WebRTC VAD, значение `4` включает использование отдельного, более грубого и строгого алгоритма VAD, основанного на вычислении мощности звуковой волны и частот пересечения нуля

---

**2.** В качестве инструмента командной строки:
```bash
python3 -m webrtcvad_wrapper.cli --mode=3 input.wav output.wav
```
или
```bash
webrtcvad_wrapper --mode=3 input.wav output.wav
```

Где:
- `--mode=3` - уровень чувствительности, целое число от `0` до `4` (если не передавать аргумент - использовать значение `3`)
- `input.wav` - имя исходной .wav аудиозаписи
- `output.wav` или `output` - шаблонное имя для .wav аудиозаписей, в которые будут сохранены найденные фрагменты с речью/звуком в формате `output_%i.wav`

В данном варианте используются следующие параметры:
- длина фрейма `10` миллисекунд
- фрагмент считается фрагментом с речью/звуком, если он содержит более `90%` фреймов, в которых WebRTC VAD (или дополнительный алгоритм VAD) нашёл речь/звук

---

Если у вас возникнут вопросы или вы хотите сотрудничать, можете написать мне на почту: vladsklim@gmail.com или в [LinkedIn](https://www.linkedin.com/in/vladklim/).