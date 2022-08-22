#!/usr/bin/python3
# -*- coding: utf-8 -*-
# OS: GNU/Linux, Author: Klim V. O.

'''
Предназначен для удаления тишины/извлечения фрагментов с речью (или другими звуками) из wav аудиозаписи.
Для работы используется py-webrtcvad (https://github.com/wiseman/py-webrtcvad).

Содержит класс VAD. Подробнее в https://github.com/Desklop/WebRTCVAD_Wrapper.

Зависимости: pydub, librosa, webrtcvad.
'''

from .webrtcvad_wrapper import VAD
