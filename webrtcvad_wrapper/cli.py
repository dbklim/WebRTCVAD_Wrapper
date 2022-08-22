#!/usr/bin/python3
# -*- coding: utf-8 -*-
# OS: GNU/Linux, Author: Klim V. O.

'''
Интерфейс командной строки для webrtcvad_wrapper.VAD().
'''

import os
import sys
from webrtcvad_wrapper import VAD


def print_help():
    print('\nИспользование: webrtcvad_wrapper.py <--mode=3> input.wav output.wav')
    print('\t--mode=3 - режим чувствительности, целое число от 0 до 4 (по умолчанию 3)')
    print('\tinput.wav - имя исходного .wav аудиофайла')
    print('\toutput.wav - шаблонное имя для .wav аудиофайлов, в которые будут сохранены найденные фрагменты с речью/звуком в формате output_%i.wav\n')
    os._exit(0)


def cli():
    if len(sys.argv) > 2 and sys.argv[1].rfind('.wav') != -1 and os.path.exists(sys.argv[1]):
        vad = VAD()
        audio = vad.read_wav(sys.argv[1])
        filtered_segments = vad.filter(audio)
        segments_with_voice = [[filtered_segment[0], filtered_segment[1]] for filtered_segment in filtered_segments if filtered_segment[-1]]
        for i, segment in enumerate(segments_with_voice):
            if sys.argv[2].rfind('.wav') != -1:
                f_name_segment = sys.argv[2][:sys.argv[2].rfind('.wav')] + '_%i.wav' % (i + 1)
            else:
                f_name_segment = sys.argv[2] + '_%i.wav' % (i + 1)
            print('Сохранение %s' % (f_name_segment))
            vad.write_wav(f_name_segment, audio[segment[0]*1000:segment[1]*1000])
    elif len(sys.argv) > 1 and sys.argv[1].find('--mode') != -1:
        sensitivity_mode = int(sys.argv[1][sys.argv[1].find('--mode=')+7:])
        if len(sys.argv) > 3 and sys.argv[2].rfind('.wav') != -1 and os.path.exists(sys.argv[2]):
            vad = VAD(sensitivity_mode)
            audio = vad.read_wav(sys.argv[2])
            filtered_segments = vad.filter(audio)
            segments_with_voice = [[filtered_segment[0], filtered_segment[1]] for filtered_segment in filtered_segments if filtered_segment[-1]]
            for i, segment in enumerate(segments_with_voice):
                if sys.argv[3].rfind('.wav') != -1:
                    f_name_segment = sys.argv[3][:sys.argv[3].rfind('.wav')] + '_%i.wav' % (i + 1)
                else:
                    f_name_segment = sys.argv[3] + '_%i.wav' % (i + 1)
                print('Сохранение %s' % (f_name_segment))
                vad.write_wav(f_name_segment, audio[segment[0]*1000:segment[1]*1000])
        else:
            print_help()
    else:
        print_help()


if __name__ == '__main__':
    cli()