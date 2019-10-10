#!/usr/bin/python3
# -*- coding: utf-8 -*-
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#       OS : GNU/Linux Ubuntu 16.04 or 18.04
# LANGUAGE : Python 3.5.2 or later
#   AUTHOR : Klim V. O.
#     DATE : 10.10.2019
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

'''
Предназначен для удаления тишины/извлечения фрагментов с речью (или другими звуками) из wav аудиозаписи.
Для работы используется py-webrtcvad (https://github.com/wiseman/py-webrtcvad).

Содержит классы Frame и WebRTCVAD. Подробнее в https://github.com/Desklop/WebRTCVAD_Wrapper.

Зависимости: pydub, webrtcvad.
'''

import os
import sys
import collections
from pydub import AudioSegment
import webrtcvad


__version__ = 1.0


class Frame(object):
    ''' Представление фрейма в аудиозаписи. Содержит поля bytes, timestamp и duration. '''
    def __init__(self, bytes_data, timestamp, duration):
        self.bytes = bytes_data
        self.timestamp = timestamp
        self.duration = duration


class WebRTCVAD:
    ''' Предоставляет методы для упрощения работы с WebRTC VAD:
    - read_wav(): загрузка .wav аудиозаписи и приведение её в поддерживаемый формат
    - write_wav(): сохранение найденных фрагментов в .wav аудиозапись
    - get_frames(): извлечение фреймов с необходимым смещением
    - filter_frames(): обработка вывода webrtcvad.Vad()is_speech()
    - filter(): объединяет get_frames() и filter_frames()
    - set_mode(): установка чувствительности WebRTC VAD

    1. sensitivity_mode - целое число от 0 до 3, чем больше - тем выше чувствительность

    Оптимальное значение для качественных данных без шумов с высокой громкостью речи - 3. '''

    sample_width = 2
    channels = 1
    def __init__(self, sensitivity_mode=3):
        self.vad = webrtcvad.Vad()
        self.set_mode(sensitivity_mode)


    def set_mode(self, sensitivity_mode=3):
        ''' Установка уровня "агрессивности"/чувствительности.
        1. sensitivity_mode - целое число от 0 до 3, чем больше - тем выше чувствительность
        
        Оптимальное значение для качественных данных без шумов с высокой громкостью речи - 3. '''

        self.vad.set_mode(sensitivity_mode)


    def filter(self, audio, frame_duration_ms=10, sample_rate=None, padding_duration_ms=50, voice_frames_threshold=0.9):
        ''' Получить фреймы из аудиозаписи и отфильтровать их. Использует скользящее окно для фильтрации: если более 90%
        фреймов в окне содержат звук, то данное окно помечается как окно с речью. Окно дополняется спереди и сзади на padding_duration_ms,
        что бы обеспечить небольшую тишину в начале и конце или что бы отрывок речи был полным.

        1. audio - объект pydub.AudioSegment с аудиозаписью или байтовая строка
        2. frame_duration_ms - длина фрейма в миллисекундах (поддерживается только 10, 20 и 30 мс)
        3. sample_rate - частота дискретизации (8, 16, 32 и 48кГц), только если audio - байтовая строка
        4. padding_duration_ms - длина дополняемых спереди и сзади частей в миллисекундах
        5. voice_frames_threshold - порог количества фреймов со звуком в окне
        6. возвращает список из tuple формата (True/False (где True: речь найдена), [список фреймов webrtcvad_wrapper.Frame])

        Оптимальные значения для качественных данных без шумов с высокой громкостью речи:
            padding_duration_ms - 50 мс
            frame_duration_ms - 10 мс '''

        frames = self.get_frames(audio, frame_duration_ms, sample_rate)
        filtered_segments = self.filter_frames(frames, padding_duration_ms, voice_frames_threshold)
        return filtered_segments


    def filter_frames(self, frames, padding_duration_ms=50, voice_frames_threshold=0.9):
        ''' Фильтрация фреймов по наличию речи или каких-либо звуков. Использует скользящее окно для фильтрации: если более 90%
        фреймов в окне содержат звук, то данное окно помечается как окно с речью. Окно дополняется спереди и сзади на padding_duration_ms,
        что бы обеспечить небольшую тишину в начале и конце или что бы отрывок речи был полным.

        1. frames - список объектов vad_utils.Frame
        2. padding_duration_ms - длина дополняемых спереди и сзади частей в миллисекундах
        3. voice_frames_threshold - порог количества фреймов со звуком в окне
        4. возвращает список из tuple формата (True/False (где True: речь найдена), [список фреймов webrtcvad_wrapper.Frame])

        Оптимальное значение padding_duration_ms для качественных данных без шумов с высокой громкостью речи - 50 мс. '''

        validations_sample_rate = [int(1 / frame.duration * len(frame.bytes) / 2) for frame in frames]
        if not validations_sample_rate[1:] == validations_sample_rate[:-1]:
            raise ValueError("[E] 'frames' имеют разный sample_rate")
        sample_rate = validations_sample_rate[0]

        validations_frame_duration = [int(frame.duration * 1000) for frame in frames]
        if not validations_frame_duration[1:] == validations_frame_duration[:-1]:
            raise ValueError("[E] 'frames' имеют разную длину")
        frame_duration_ms = validations_frame_duration[0]

        if voice_frames_threshold > 1 or voice_frames_threshold < 0.01:
            raise ValueError("[E] 'voice_frames_threshold' имеет недопустимое значение: " + str(voice_frames_threshold))

        num_padding_frames = int(padding_duration_ms / frame_duration_ms)
        # Используется deque для буфера окна
        window_buffer = collections.deque(maxlen=num_padding_frames)

        # Есть два состояния: триггерное и нетриггерное. В самом начале установлено нетриггерное состояние
        triggered = False
        filtered_segments = []
        filtered_segments.append([triggered, []])
        for frame in frames:
            is_speech = self.vad.is_speech(frame.bytes, sample_rate)
            if not triggered:
                window_buffer.append((frame, is_speech))
                num_voiced = len([frame for frame, speech in window_buffer if speech])
                # Если больше 90% фреймов в окне содержат звук, то переход в триггерное состояние
                if num_voiced > voice_frames_threshold * window_buffer.maxlen:
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
                if num_unvoiced > voice_frames_threshold * window_buffer.maxlen:
                    triggered = False
                    filtered_segments[-1][1] = filtered_segments[-1][1][:len(filtered_segments[-1][1])-window_buffer.maxlen+1]
                    filtered_segments.append([triggered, [window_frame[0] for window_frame in window_buffer]])
                    window_buffer.clear()
                else:
                    filtered_segments[-1][1].append(frame)
        if len(filtered_segments[0][1]) == 0:
            del filtered_segments[0]

        # Если не создать объект Vad() заново, то в последующие первые несколько вызовов vad.is_speech() выдаёт True (даже если подать нулевые байты)
        # Занимает по времени примерно 1*10^-5 сек
        self.vad = webrtcvad.Vad()

        return filtered_segments
    

    def get_frames(self, audio, frame_duration_ms=10, sample_rate=None):
        ''' Получить фреймы из аудиозаписи.
        1. audio - объект pydub.AudioSegment с аудиозаписью или байтовая строка
        2. frame_duration_ms - длина фрейма в миллисекундах (поддерживается только 10, 20 и 30 мс)
        3. sample_rate - частота дискретизации (8, 16, 32 и 48кГц), только если audio - байтовая строка
        4. возвращает список из фреймов webrtcvad_wrapper.Frame заданной длины
        
        Оптимальное значение frame_duration_ms для качественных данных без шумов с высокой громкостью речи - 10 мс. '''

        if isinstance(audio, AudioSegment):
            audio_bytes = audio.raw_data
            sample_rate = audio.frame_rate
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
        while offset + frame_width < len(audio_bytes):
            frames.append(Frame(audio_bytes[offset:offset + frame_width], timestamp, duration))
            timestamp += duration
            offset += frame_width
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


    def read_wav(self, f_name_wav, sample_rate=None, return_source_sample_rate=False):
        ''' Загрузить .wav аудиозапись. Поддерживаются только моно аудиозаписи с частотой
        дискретизации 8, 16, 32 и 48кГц и 2 байта/16 бит. Если параметры у загружаемой аудиозаписи
        отличаются от указанных - она будет приведена в требуемый формат.
        1. f_name_wav - имя .wav аудиозаписи
        2. sample_rate - требуемая частота дискретизации (8, 16, 32 и 48кГц) (если None - приводится к ближайшему из поддерживаемых значений)
        3. возвращает объект pydub.AudioSegment с аудиозаписью и, если return_source_sample_rate=True, исходную частоту дискретизации аудиозаписи '''

        if f_name_wav.rfind('.wav') == -1:
            raise ValueError("[E] 'f_name_wav' должна содержать имя .wav аудиозаписи")

        audio = AudioSegment.from_wav(f_name_wav)

        source_sample_rate = audio.frame_rate
        if sample_rate is None:
            sample_rate = self.__align_sample_rate(source_sample_rate)
        elif sample_rate not in [8000, 16000, 32000, 48000]:
            sample_rate = self.__align_sample_rate(sample_rate)

        if source_sample_rate not in [8000, 16000, 32000, 48000]:
            audio = audio.set_frame_rate(sample_rate)

        if audio.sample_width != self.sample_width:
            audio = audio.set_sample_width(self.sample_width)
        if audio.channels != self.channels:
            audio = audio.split_to_mono()[0]

        if return_source_sample_rate:
            return audio, source_sample_rate
        else:
            return audio


    def write_wav(self, f_name_wav, audio_data, sample_rate=None, desired_sample_rate=None):
        ''' Сохранить .wav аудиозапись.
        1. f_name_wav - имя .wav файла, в который будет сохранена аудиозапись
        2. audio_data - может быть:
            - объект pydub.AudioSegment с аудиозаписью
            - список фреймов [vad_utils.Frame, ...]
            - байтовая строка с аудиозаписью
        3. sample_rate - частота дискретизации аудиозаписи (используется когда audio_data - байтовая строка)
        4. desired_sample_rate - желаемая частота дискретизации (если None - не менять частоту дискретизации) '''

        if isinstance(audio_data, AudioSegment):
            self.write_wav_from_audiosegment(f_name_wav, audio_data, desired_sample_rate)
        elif isinstance(audio_data, list):
            self.write_wav_from_frames(f_name_wav, audio_data, desired_sample_rate)
        elif isinstance(audio_data, bytes):
            if sample_rate is None:
                raise ValueError("[E] КОгда type(audio_data) = bytes, 'sample_rate' не может быть None")
            self.write_wav_from_bytes(f_name_wav, audio_data, sample_rate, desired_sample_rate)
        else:
            raise ValueError("[E] 'audio_data' имеет неподдерживаемый тип. Поддерживаются:\n" + \
                             "\t- объект pydub.AudioSegment с аудиозаписью\n" + \
                             "\t- список фреймов [vad_utils.Frame, ...]\n" + \
                             "\t- байтовая строка с аудиозаписью")


    def write_wav_from_audiosegment(self, f_name_wav, audio, desired_sample_rate=None):
        ''' Сохранить .wav аудиозапись.
        1. f_name_wav - имя .wav файла, в который будет сохранена аудиозапись
        2. audio - объект pydub.AudioSegment с аудиозаписью
        3. desired_sample_rate - желаемая частота дискретизации (если None - не менять частоту дискретизации) '''

        if desired_sample_rate is not None:
            audio = audio.set_frame_rate(desired_sample_rate)
        audio.export(f_name_wav, format='wav')


    def write_wav_from_frames(self, f_name_wav, frames, desired_sample_rate=None):
        ''' Сохранить .wav аудиозапись.
        1. f_name_wav - имя .wav файла, в который будет сохранена аудиозапись
        2. frames - список фреймов [vad_utils.Frame, ...]
        3. desired_sample_rate - желаемая частота дискретизации (если None - не менять частоту дискретизации) '''

        if len(frames) == 0:
            raise ValueError("[E] 'frames' не содержит элементов")

        validations_sample_rate = [int(1 / frame.duration * len(frame.bytes) / 2.0) for frame in frames]
        if not validations_sample_rate[1:] == validations_sample_rate[:-1]:
            raise ValueError('[E] Frames имеют разный sample_rate')
        sample_rate = validations_sample_rate[0]
        audio_bytes = b''.join([frame.bytes for frame in frames])

        audio = AudioSegment(data=audio_bytes, sample_width=self.sample_width, frame_rate=sample_rate, channels=self.channels)
        if desired_sample_rate is not None and desired_sample_rate != sample_rate:
            audio = audio.set_frame_rate(desired_sample_rate)

        audio.export(f_name_wav, format='wav')


    def write_wav_from_bytes(self, f_name_wav, audio_bytes, sample_rate, desired_sample_rate=None):
        ''' Сохранить .wav аудиозапись.
        1. f_name_wav - имя .wav файла, в который будет сохранена аудиозапись
        2. audio_bytes - байтовая строка с аудиозаписью
        3. sample_rate - частота дискретизации
        4. desired_sample_rate - желаемая частота дискретизации (если None - не менять частоту дискретизации) '''

        audio = AudioSegment(data=audio_bytes, sample_width=self.sample_width, frame_rate=sample_rate, channels=self.channels)
        if desired_sample_rate is not None and desired_sample_rate != sample_rate:
            audio = audio.set_frame_rate(desired_sample_rate)

        audio.export(f_name_wav, format='wav')




def main():
    vad = WebRTCVAD()
    f_name_audio = 'test_audio/test_full_vad.wav'

    # Тест корректности сохранения исходной, неподдерживаемой по умолчанию, частоты дискретизации
    audio, source_sample_rate = vad.read_wav(f_name_audio, return_source_sample_rate=True)
    filtered_segments = vad.filter(audio)

    segments_with_voice = [filtered_segment[1] for filtered_segment in filtered_segments if filtered_segment[0]]
    for j, segment in enumerate(segments_with_voice):
        f_name_segment = 'segment1_%002d.wav' % (j + 1)
        print('Сохранение %s' % (f_name_segment))
        vad.write_wav(f_name_segment, segment, desired_sample_rate=source_sample_rate)

    #------------#

    f_name_audio = 'test_audio/test_fa_vad.wav'

    # Тест корректности работы VAD
    audio = vad.read_wav(f_name_audio)
    frames = vad.get_frames(audio)
    filtered_segments = vad.filter_frames(frames)

    segments_with_voice = [filtered_segment[1] for filtered_segment in filtered_segments if filtered_segment[0]]
    for j, segment in enumerate(segments_with_voice):
        f_name_segment = 'segment2_%002d.wav' % (j + 1)
        print('Сохранение %s' % (f_name_segment))
        vad.write_wav(f_name_segment, segment)
    
    # Перевод фреймов в байтовую строку (без заголовков .wav, чисто данные):
    # audio_bytes = b''.join([frame.bytes for frame in frames])


if __name__ == '__main__':
    main()