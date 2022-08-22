#!/usr/bin/python3
# -*- coding: utf-8 -*-
# OS: GNU/Linux, Author: Klim V. O.

'''
Предназначен для удаления тишины/извлечения фрагментов с речью (или другими звуками) из wav аудиозаписи.
Для работы используется py-webrtcvad (https://github.com/wiseman/py-webrtcvad).

Содержит класс VAD. Подробнее в https://github.com/Desklop/WebRTCVAD_Wrapper.

Зависимости: pydub, librosa, webrtcvad.
'''

import collections
from pydub import AudioSegment
import webrtcvad
import librosa
import numpy as np


__version__ = 1.4


class Frame(object):
    ''' Представление фрейма в аудиозаписи. Содержит поля bytes, timestamp и duration. '''
    def __init__(self, bytes_data, timestamp, duration):
        self.bytes = bytes_data
        self.timestamp = timestamp
        self.duration = duration


class VAD:
    ''' Предоставляет методы для упрощения работы с WebRTC VAD:
    - read_wav(): загрузка .wav аудиозаписи и приведение её в поддерживаемый формат
    - write_wav(): сохранение .wav аудиозаписи
    - filter(): разбиение аудиозаписи на фреймы и их фильтрация по наличию речи/звука
    - set_mode(): установка чувствительности WebRTC VAD и включение дополнительного агрессивного режима

    1. sensitivity_mode - целое число от 0 до 4, чем больше - тем выше чувствительность

    Значения от 0 до 3 являются базовыми для WebRTC VAD, значение 4 включает использование отдельного,
    более грубого и строгого алгоритма, основанного на вычислении мощности звуковой волны и частот пересечения нуля.

    Уровень чувствительности 4 предназначен в первую очередь для предобработки аудиозаписей для нейронных сетей (но не для распознавания речи),
    так как он часто игнорирует вообще всё, кроме гласных и звонких согласных звуков в речи (или просто громких звуков).

    Оптимальное значение для качественных данных без шумов с высокой громкостью речи - 3. '''

    sample_width = 2
    channels = 1
    def __init__(self, sensitivity_mode=3):
        self.set_mode(sensitivity_mode)


    def set_mode(self, sensitivity_mode=3):
        ''' Установка уровня "агрессивности"/чувствительности.
        1. sensitivity_mode - целое число от 0 до 4, чем больше - тем выше чувствительность

        Значения от 0 до 3 являются базовыми для WebRTC VAD, значение 4 включает использование отдельного,
        более грубого и строгого алгоритма, основанного на вычислении мощности звуковой волны и частот пересечения нуля.
        
        Оптимальное значение для качественных данных без шумов с высокой громкостью речи - 3. '''

        self.sensitivity_mode = sensitivity_mode


    def filter(self, audio, frame_duration_ms=10, sample_rate=None, padding_duration_ms=50, threshold_voice_frames=0.9, threshold_rms=0.1, threshold_zcr=0.5):
        ''' Разбить аудиозапись на фреймы и отфильтровать их по наличию речи/звука.
        
        Если sensitivity_mode=0..3:\n
        Использует скользящее окно для фильтрации: если более 90% фреймов в окне содержат звук, то данное окно помечается как окно с речью.
        Окно дополняется спереди и сзади на padding_duration_ms, что бы обеспечить небольшую тишину в начале и конце или что бы отрывок речи был полным.
        Затем сохранённые фреймы переводятся во временные метки в исходной аудиозаписи.
        В данном режиме аргументы threshold_rms и threshold_zcr игнорируются.

        ВНИМАНИЕ! Если длина аудиозаписи не кратна размеру 1 фрейма - она будет дополнена нулями до необходимой длины (справедливо только при
        sensitivity_mode=0..3).

        Если sensitivity_mode=4:\n
        Метод агрессивный, часто игнорирует вообще всё, кроме гласных и звонких согласных звуков в речи (или просто громких звуков). Фильтрация работает так:
        на основе RMS (root-mean-square, отражает мощность звуковой волны) и ZCR (zero-crossing rate, частоты пересечения нуля) по заданным порогам
        фильтруются фреймы, которые затем переводятся во временные метки в исходной аудиозаписи.
        В данном режиме аргументы padding_duration_ms и threshold_voice_frames игнорируются.

        sensitivity_mode можно задать через метод set_mode().

        ВНИМАНИЕ! Поддерживаются только моно аудиозаписи с шириной семпла 2 байта.

        1. audio - объект pydub.AudioSegment с аудиозаписью или байтовая строка с аудиоданными (без заголовков wav)
        2. frame_duration_ms - длина фрейма в миллисекундах (поддерживается только 10, 20 и 30 мс)
        3. sample_rate - частота дискретизации (поддерживается только 8, 16, 32 или 48кГц):
            когда audio - объект pydub.AudioSegment и частота дискретизации None или не поддерживается - будет приведена к ближайшей из поддерживаемых
            когда audio - байтовая строка, частота дискретизации должна быть задана и поддерживаться
        4. padding_duration_ms - длина дополняемых спереди и сзади частей в миллисекундах
        5. threshold_voice_frames - порог количества фреймов со звуком в окне
        6. threshold_rms - порог определения речи (порог RMS) (только когда sensitivity_mode=4)
        7. threshold_zcr - порог определения тишины (порог ZRC) (только когда sensitivity_mode=4)
        8. возвращает список из списков с границами сегментов следующего формата:
        [
            [0.00, 1.23, True/False],
            ...
        ]\n
        Где:
            0.00 - начало сегмента (в секундах)
            1.23 - конец сегмента (в секундах)
            True/False - True: речь/звук, False: тишина

        Оптимальные значения для качественных данных без шумов с высокой громкостью речи:
            padding_duration_ms - 50 мс
            frame_duration_ms - 10 мс '''

        if self.sensitivity_mode < 4:
            frames = self.__get_frames(audio, frame_duration_ms, sample_rate)
            filtered_segments = self.__filter_frames(frames, padding_duration_ms, threshold_voice_frames)
        else:
            filtered_segments = self.rough_filter(audio, frame_duration_ms, sample_rate, threshold_rms, threshold_zcr)
        return filtered_segments


    def rough_filter(self, audio, frame_duration_ms=10, sample_rate=None, threshold_rms=0.1, threshold_zcr=0.5):
        ''' Разбить аудиозапись на фреймы и отфильтровать их по наличию речи/звука. Метод агрессивный, часто игнорирует вообще всё, кроме
        гласных и звонких согласных звуков в речи (или просто громких звуков).
        
        Фильтрация работает так: на основе RMS (root-mean-square, отражает мощность звуковой волны) и ZCR (zero-crossing rate, частоты пересечения нуля)
        по заданным порогам фильтруются фреймы, которые затем переводятся во временные метки в исходной аудиозаписи.

        1. audio - объект pydub.AudioSegment с аудиозаписью или байтовая строка с аудиоданными (без заголовков wav)
        2. frame_duration_ms - длина фрейма в миллисекундах (рекомендуются значения 10, 20 или 30 мс)
        3. sample_rate - частота дискретизации, только если audio - байтовая строка
        4. threshold_rms - порог определения речи (порог RMS)
        5. threshold_zcr - порог определения тишины (порог ZCR)
        6. возвращает список из списков с границами сегментов следующего формата:
        [
            [0.00, 1.23, True/False],
            ...
        ]\n
        Где:
            0.00 - начало сегмента
            1.23 - конец сегмента
            True/False - True: речь/звук, False: тишина '''

        if isinstance(audio, AudioSegment):
            audio_data = np.array(audio.get_array_of_samples())
            audio_data = audio_data.astype(np.float64)
            audio_data = librosa.util.normalize(audio_data, axis=0)
            sample_rate = audio.frame_rate
        elif isinstance(audio, bytes):
            if self.sample_width != 2:
                raise ValueError("[E] Когда type(audio) == bytes, 'sample_width' должен быть равен 2 байтам (16 бит)")
            audio_data = np.frombuffer(audio, dtype=np.int16)
            audio_data = audio_data.astype(np.float64)
            audio_data = librosa.util.normalize(audio_data, axis=0)
            if sample_rate is None:
                raise ValueError("[E] Когда type(audio) == bytes, 'sample_rate' не может быть None")
        else:
            raise ValueError("[E] 'audio' может быть только AudioSegment или bytes")

        frame_len = int(frame_duration_ms * sample_rate / 1000)
        frame_shift = int(frame_duration_ms / 2 * sample_rate / 1000)

        # Вычисление RMS (отражает мощность звуковой волны)
        rms = librosa.feature.rms(y=audio_data, frame_length=frame_len, hop_length=frame_shift)
        rms = rms[0]
        rms = librosa.util.normalize(rms, axis=0)

        # Вычисление частот пересечения нуля
        zcr = librosa.feature.zero_crossing_rate(audio_data, frame_length=frame_len, hop_length=frame_shift, threshold=0)
        zcr = zcr[0]

        # Фильтрация значений RMS и ZRC по заданным порогам и сохранение номеров фреймов, содержащих речь/звук
        # Идентично этому:
        # ff = []
        # for i in range(0,len(rms)):
        #     if ((rms[i] > threshold_rms) | (zrc[i] > threshold_zcr)):
        #          ff.append(i)
        voice_frame_numbers = np.where((rms > threshold_rms) | (zcr > threshold_zcr))[0]

        # Определение границ речи/звука
        start_voice_frame_numbers = [voice_frame_numbers[0]]
        end_voice_frame_numbers = []

        shapeofidxs = np.shape(voice_frame_numbers)
        for i in range(shapeofidxs[0]-1):
            if (voice_frame_numbers[i + 1] - voice_frame_numbers[i]) != 1:
                end_voice_frame_numbers.append(voice_frame_numbers[i])
                start_voice_frame_numbers.append(voice_frame_numbers[i+1])
        end_voice_frame_numbers.append(voice_frame_numbers[-1])

        # Удаление последней границы, если её начало совпадает с концом
        if end_voice_frame_numbers[-1] == start_voice_frame_numbers[-1]:
            end_voice_frame_numbers.pop()
            start_voice_frame_numbers.pop()
        if len(start_voice_frame_numbers) != len(end_voice_frame_numbers):
            raise ValueError('[E] Найденные границы с речью/звуком не совпадают')

        # Перевод номеров фреймов во временные метки
        start_voice_frame_numbers = np.array(start_voice_frame_numbers)
        end_voice_frame_numbers = np.array(end_voice_frame_numbers)

        start_borders = start_voice_frame_numbers * frame_shift / sample_rate
        end_borders = end_voice_frame_numbers * frame_shift / sample_rate

        segments_with_voice = [[round(start_border, 2), round(end_border, 2), True] for start_border, end_border in zip(start_borders, end_borders)]
        len_audio = round(len(audio_data) / sample_rate, 2)

        # Дополнение временных меток с голосом/звуком остальными участками аудиозаписи
        filtered_segments_spans = []
        if segments_with_voice[0][0] != 0.00:
            filtered_segments_spans.append([0.00, segments_with_voice[0][0], False])

        for j in range(len(segments_with_voice)-1):
            filtered_segments_spans.append(segments_with_voice[j])
            filtered_segments_spans.append([segments_with_voice[j][1], segments_with_voice[j+1][0], False])
        filtered_segments_spans.append(segments_with_voice[-1])

        if filtered_segments_spans[-1][1] != len_audio:
            filtered_segments_spans.append([segments_with_voice[-1][1], len_audio, False])

        return filtered_segments_spans


    def __filter_frames(self, frames, padding_duration_ms=50, threshold_voice_frames=0.9):
        ''' Фильтрация фреймов по наличию речи или каких-либо звуков. Использует скользящее окно для фильтрации: если более 90%
        фреймов в окне содержат звук, то данное окно помечается как окно с речью. Окно дополняется спереди и сзади на padding_duration_ms,
        что бы обеспечить небольшую тишину в начале и конце или что бы отрывок речи был полным.

        1. frames - список объектов webrtcvad_wrapper.Frame
        2. padding_duration_ms - длина дополняемых спереди и сзади частей в миллисекундах
        3. threshold_voice_frames - порог количества фреймов со звуком в окне
        4. возвращает список из списков с границами сегментов следующего формата:
        [
            [0.00, 1.23, True/False],
            ...
        ]
        Где:
            0.00 - начало сегмента
            1.23 - конец сегмента
            True/False - True: речь/звук, False: тишина

        Оптимальное значение padding_duration_ms для качественных данных без шумов с высокой громкостью речи - 50 мс. '''

        validations_sample_rate = [int(1 / frame.duration * len(frame.bytes) / 2) for frame in frames]
        if not validations_sample_rate[1:] == validations_sample_rate[:-1]:
            raise ValueError("[E] 'frames' имеют разный sample_rate")
        sample_rate = validations_sample_rate[0]

        validations_frame_duration = [int(frame.duration * 1000) for frame in frames]
        if not validations_frame_duration[1:] == validations_frame_duration[:-1]:
            raise ValueError("[E] 'frames' имеют разную длину")
        frame_duration_ms = validations_frame_duration[0]

        if threshold_voice_frames > 1 or threshold_voice_frames < 0.01:
            raise ValueError("[E] 'threshold_voice_frames' имеет недопустимое значение: " + str(threshold_voice_frames))

        num_padding_frames = int(padding_duration_ms / frame_duration_ms)
        # Используется deque для буфера окна
        window_buffer = collections.deque(maxlen=num_padding_frames)

        # Это костыль. Если не создать объект webrtcvad.Vad() каждый раз заново или не 'обновлять' уровень чувствительности, то в следующие первые
        # несколько (обычно 2-15) вызовов vad.is_speech() выдаёт True вне зависимости от переданных данных (даже если подать нулевые байты)
        # Занимает по времени примерно 5-10*10^-6 сек (0.000005-0.00001 сек)
        vad = webrtcvad.Vad(self.sensitivity_mode)

        # Есть два состояния: триггерное и нетриггерное. В самом начале установлено нетриггерное состояние
        triggered = False
        filtered_segments = []
        filtered_segments.append([triggered, []])
        for frame in frames:
            is_speech = vad.is_speech(frame.bytes, sample_rate)
            if not triggered:
                window_buffer.append((frame, is_speech))
                num_voiced = len([frame for frame, speech in window_buffer if speech])
                # Если больше 90% фреймов в окне содержат звук, то переход в триггерное состояние
                if num_voiced > threshold_voice_frames * window_buffer.maxlen:
                    triggered = True
                    filtered_segments[-1][1] = filtered_segments[-1][1][:len(filtered_segments[-1][1])-window_buffer.maxlen+1]
                    filtered_segments.append([triggered, [window_frame[0] for window_frame in window_buffer]])
                    window_buffer.clear()
                else:
                    filtered_segments[-1][1].append(frame)
            else:
                # Триггерное состояние. Заполнение буфера фреймами
                window_buffer.append((frame, is_speech))
                num_unvoiced = len([f for f, speech in window_buffer if not speech])
                # Если больше 90% фреймов в буфере не содержат звук, то переход в нетриггерное состояние
                if num_unvoiced > threshold_voice_frames * window_buffer.maxlen:
                    triggered = False
                    filtered_segments[-1][1] = filtered_segments[-1][1][:len(filtered_segments[-1][1])-window_buffer.maxlen+1]
                    filtered_segments.append([triggered, [window_frame[0] for window_frame in window_buffer]])
                    window_buffer.clear()
                else:
                    filtered_segments[-1][1].append(frame)
        if len(filtered_segments[0][1]) == 0:
            del filtered_segments[0]

        filtered_segments_spans = []
        for i in range(len(filtered_segments)):
            len_segment = len(filtered_segments[i][1]) * filtered_segments[i][1][0].duration
            if i == 0:
                start = 0.0
                end = len_segment
            else:
                start = filtered_segments_spans[-1][1]
                end = start + len_segment
            filtered_segments_spans.append([round(start, 2), round(end, 2), filtered_segments[i][0]])

        del vad
        return filtered_segments_spans


    def __get_frames(self, audio, frame_duration_ms=10, sample_rate=None):
        ''' Получить фреймы из аудиозаписи.
        
        ВНИМАНИЕ! Если длина аудиозаписи не кратна размеру 1 фрейма - она будет дополнена нулями до необходимой длины.

        1. audio - объект pydub.AudioSegment с аудиозаписью или байтовая строка с аудиоданными (без заголовков wav)
        2. frame_duration_ms - длина фрейма в миллисекундах (поддерживается только 10, 20 и 30 мс)
        3. sample_rate - частота дискретизации (поддерживается только 8, 16, 32 или 48кГц):
            когда audio - объект pydub.AudioSegment и частота дискретизации None или не поддерживается - будет приведена к ближайшей из поддерживаемых
            когда audio - байтовая строка, частота дискретизации должна быть задана и поддерживаться
        4. возвращает список из фреймов webrtcvad_wrapper.Frame заданной длины

        Оптимальное значение frame_duration_ms для качественных данных без шумов с высокой громкостью речи - 10 мс. '''

        if isinstance(audio, AudioSegment):
            sample_rate = audio.frame_rate
            if sample_rate not in [8000, 16000, 32000, 48000]:
                sample_rate = self.__align_sample_rate(sample_rate)
                audio = audio.set_frame_rate(sample_rate)
                sample_rate = audio.frame_rate
            audio_bytes = audio.raw_data
        elif isinstance(audio, bytes):
            audio_bytes = audio
            if sample_rate is None:
                raise ValueError("[E] Когда type(audio) == bytes, 'sample_rate' не может быть None")
        else:
            raise ValueError("[E] 'audio' может быть только AudioSegment или bytes")

        if frame_duration_ms not in [10, 20, 30]:
            raise ValueError("[E] 'frame_duration_ms' может быть только 10, 20 и 30 миллисекунд")

        if sample_rate not in [8000, 16000, 32000, 48000]:
            raise ValueError("[E] 'sample_rate' может быть только 8000, 16000, 32000 и 48000 Гц")

        frame_width = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
        offset = 0
        timestamp = 0.0
        duration = (float(frame_width) / sample_rate) / 2.0
        frames = []
        while offset + frame_width <= len(audio_bytes):
            frames.append(Frame(audio_bytes[offset:offset + frame_width], timestamp, duration))
            timestamp += duration
            offset += frame_width
        if len(audio_bytes) % frame_width != 0 and offset + frame_width > len(audio_bytes):
            frames.append(Frame(audio_bytes[offset:]+b'\x00'*(offset+frame_width-len(audio_bytes)), timestamp, duration))
        return frames


    def __align_sample_rate(self, source_sample_rate):
        ''' Приведение частоты дискретизации к ближайшей из поддерживаемых: 8, 16, 32 или 48кГц.
        1. source_sample_rate - исходная частота дискретизации в Гц
        2. возвращает исправленную частоту дискретизации '''

        if source_sample_rate > 48000:
            sample_rate = 48000
        elif source_sample_rate > 32000 and source_sample_rate < 48000:
            sample_rate = 32000
        elif source_sample_rate > 16000 and source_sample_rate < 32000:
            sample_rate = 16000
        else:
            sample_rate = 8000
        return sample_rate


    def read_wav(self, f_name_wav, sample_rate=None):
        ''' Загрузить .wav аудиозапись. Поддерживаются только моно аудиозаписи 2 байта/16 бит. Если параметры у загружаемой аудиозаписи
        отличаются от указанных - она будет приведена в требуемый формат.
        1. f_name_wav - имя .wav аудиозаписи или BytesIO
        2. sample_rate - желаемая частота дискретизации (если None - не менять частоту дискретизации)
        3. возвращает объект pydub.AudioSegment с аудиозаписью '''

        if isinstance(f_name_wav, str) and f_name_wav.rfind('.wav') == -1:
            raise ValueError("[E] 'f_name_wav' должна содержать имя .wav аудиозаписи")

        audio = AudioSegment.from_wav(f_name_wav)

        if sample_rate is not None:
            audio = audio.set_frame_rate(sample_rate)
        if audio.sample_width != self.sample_width:
            audio = audio.set_sample_width(self.sample_width)
        if audio.channels != self.channels:
            audio = audio.set_channels(self.channels)
        return audio


    def write_wav(self, f_name_wav, audio_data, sample_rate=None):
        ''' Сохранить .wav аудиозапись.
        1. f_name_wav - имя .wav аудиозаписи, в который будет сохранена аудиозапись или BytesIO
        2. audio_data - может быть:
            - объект pydub.AudioSegment с аудиозаписью
            - байтовая строка с аудиозаписью (без заголовков wav)
        3. sample_rate - частота дискретизации аудиозаписи:
            когда audio_data - байтовая строка, должна соответствовать реальной частоте дискретизации аудиозаписи
            в остальных случаях частота дискретизации будет приведена к указанной (если None - не менять частоту дискретизации) '''

        if isinstance(audio_data, AudioSegment):
            self.write_wav_from_audiosegment(f_name_wav, audio_data, sample_rate)
        elif isinstance(audio_data, bytes):
            if sample_rate is None:
                raise ValueError("[E] Когда type(audio_data) = bytes, 'sample_rate' не может быть None")
            self.write_wav_from_bytes(f_name_wav, audio_data, sample_rate)
        else:
            raise ValueError("[E] 'audio_data' имеет неподдерживаемый тип. Поддерживаются:\n" + \
                             "\t- объект pydub.AudioSegment с аудиозаписью\n" + \
                             "\t- байтовая строка с аудиозаписью")


    def write_wav_from_audiosegment(self, f_name_wav, audio, desired_sample_rate=None):
        ''' Сохранить .wav аудиозапись.
        1. f_name_wav - имя .wav файла, в который будет сохранена аудиозапись или BytesIO
        2. audio - объект pydub.AudioSegment с аудиозаписью
        3. desired_sample_rate - желаемая частота дискретизации (если None - не менять частоту дискретизации) '''

        if desired_sample_rate is not None:
            audio = audio.set_frame_rate(desired_sample_rate)
        audio.export(f_name_wav, format='wav')


    def write_wav_from_bytes(self, f_name_wav, audio_bytes, sample_rate, desired_sample_rate=None):
        ''' Сохранить .wav аудиозапись.
        1. f_name_wav - имя .wav файла, в который будет сохранена аудиозапись или BytesIO
        2. audio_bytes - байтовая строка с аудиозаписью (без заголовков wav)
        3. sample_rate - частота дискретизации
        4. desired_sample_rate - желаемая частота дискретизации (если None - не менять частоту дискретизации) '''

        audio = AudioSegment(data=audio_bytes, sample_width=self.sample_width, frame_rate=sample_rate, channels=self.channels)
        if desired_sample_rate is not None and desired_sample_rate != sample_rate:
            audio = audio.set_frame_rate(desired_sample_rate)

        audio.export(f_name_wav, format='wav')




def main():
    # Тест корректности работы WebRTC VAD на неподдерживаемой по умолчанию аудио
    vad = VAD()
    f_name_audio = 'test_audio/test_vad_1.wav'
    audio = vad.read_wav(f_name_audio)
    filtered_segments = vad.filter(audio)

    segments_with_voice = [[filtered_segment[0], filtered_segment[1]] for filtered_segment in filtered_segments if filtered_segment[-1]]
    for i, segment in enumerate(segments_with_voice):
        f_name_segment = 'segment1_%002d.wav' % (i + 1)
        print('Сохранение %s' % (f_name_segment))
        vad.write_wav(f_name_segment, audio[segment[0]*1000:segment[1]*1000])

    # Тест дополнительного агрессивного режима (sensitivity_mode=4)
    vad.set_mode(4)
    filtered_segments = vad.filter(audio.raw_data, sample_rate=audio.frame_rate)

    segments_with_voice = [[filtered_segment[0], filtered_segment[1]] for filtered_segment in filtered_segments if filtered_segment[-1]]
    audio_without_silence = audio[segments_with_voice[0][0]*1000:segments_with_voice[0][1]*1000]
    for segment in segments_with_voice[1:]:
        audio_without_silence += audio[segment[0]*1000:segment[1]*1000]
    f_name_segment = 'segment_without_silence.wav'
    print('Сохранение %s' % f_name_segment)
    vad.write_wav(f_name_segment, audio_without_silence)

    # Тест корректности работы WebRTC VAD
    f_name_audio = 'test_audio/test_vad_2.wav'
    vad.set_mode(3)
    audio = vad.read_wav(f_name_audio)
    filtered_segments = vad.filter(audio)

    segments_with_voice = [[filtered_segment[0], filtered_segment[1]] for filtered_segment in filtered_segments if filtered_segment[-1]]
    for i, segment in enumerate(segments_with_voice):
        f_name_segment = 'segment2_%002d.wav' % (i + 1)
        print('Сохранение %s' % (f_name_segment))
        vad.write_wav(f_name_segment, audio[segment[0]*1000:segment[1]*1000])


if __name__ == '__main__':
    main()
