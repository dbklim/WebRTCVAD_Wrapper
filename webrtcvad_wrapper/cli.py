#!/usr/bin/python3
# -*- coding: utf-8 -*-
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#       OS : GNU/Linux Ubuntu 16.04 or 18.04
# LANGUAGE : Python 3.5.2 or later
#   AUTHOR : Klim V. O.
#     DATE : 10.10.2019
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

'''
Интерфейс командной строки для webrtcvad_wrapper.WebRTCVAD().
'''

import os
import sys
from webrtcvad_wrapper import WebRTCVAD


def print_help():
    print('\nИспользование: webrtcvad_wrapper.py input.wav output.wav')
    print('\tinput.wav - имя исходного .wav аудиофайла')
    print('\toutput.wav - шаблонное имя для .wav аудиофайлов, в которые будут сохранены найденные фрагменты с речью/звуком в формате output_%i.wav\n')
    os._exit(0)


def cli():
    if len(sys.argv) > 1 and sys.argv[1].rfind('.wav') != -1 and os.path.exists(sys.argv[1]):
        if len(sys.argv) > 2:
            vad = WebRTCVAD()
            audio, source_sample_rate = vad.read_wav(sys.argv[1], return_source_sample_rate=True)
            filtered_segments = vad.filter(audio)
            segments_with_voice = [filtered_segment[1] for filtered_segment in filtered_segments if filtered_segment[0]]
            for j, segment in enumerate(segments_with_voice):
                if sys.argv[2].rfind('.wav') != -1:
                    f_name_segment = sys.argv[2][:sys.argv[2].rfind('.wav')] + '_%i.wav' % (j + 1)
                else:
                    f_name_segment = sys.argv[2] + '_%i.wav' % (j + 1)
                print("Сохранение в %s" % (f_name_segment))
                vad.write_wav(f_name_segment, segment, desired_sample_rate=source_sample_rate)
            return
        else:
            print_help()
    else:
        print_help()


if __name__ == '__main__':
    cli()