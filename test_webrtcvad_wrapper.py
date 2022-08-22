#!/usr/bin/python3
# -*- coding: utf-8 -*-
# OS: GNU/Linux, Author: Klim V. O.

'''
Тесты для WebRTCVAD_Wrapper.
'''

import os
import platform
import signal
from webrtcvad_wrapper import VAD


def main():
    result_tests = []

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
    if len(segments_with_voice) == 3:
        result_tests.append(True)
        print('OK')
    else:
        result_tests.append(False)

    # Тест дополнительного агрессивного режима (sensitivity_mode=4)
    vad.set_mode(4)
    filtered_segments = vad.filter(audio)

    segments_with_voice = [[filtered_segment[0], filtered_segment[1]] for filtered_segment in filtered_segments if filtered_segment[-1]]
    audio_without_silence = audio[segments_with_voice[0][0]*1000:segments_with_voice[0][1]*1000]
    for segment in segments_with_voice[1:]:
        audio_without_silence += audio[segment[0]*1000:segment[1]*1000]
    f_name_segment = 'segment_without_silence.wav'
    print('Сохранение %s' % f_name_segment)
    vad.write_wav(f_name_segment, audio_without_silence)
    if len(audio_without_silence) == 2180:
        result_tests.append(True)
        print('OK')
    else:
        result_tests.append(False)

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
    if len(segments_with_voice) == 5:
        result_tests.append(True)
        print('OK')
    else:
        result_tests.append(False)
    
    if all(result_tests):
        print('\nALL OK')


def on_stop(*args):
    print('\n[i] Остановлено')
    os._exit(0)


if __name__ == '__main__':
    # При нажатии комбинаций Ctrl+Z, Ctrl+C либо закрытии терминала будет вызываться функция on_stop() (Работает только на linux системах!)
    if platform.system() == 'Linux':
        for sig in (signal.SIGTSTP, signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, on_stop)
    main()