#!/usr/bin/env python

# Python wrapper for METEOR implementation, by Xinlei Chen
# Acknowledge Michael Denkowski for the generous discussion and help

import os
import sys
import subprocess
import threading

# Assumes meteor-1.5.jar is in the same directory as meteor.py.  Change as needed.
METEOR_JAR = 'meteor-1.5.jar'


class Meteor:

    def __init__(self):
        self.meteor_cmd = ['java', '-jar', '-Xmx2G', METEOR_JAR,
                           '-', '-', '-stdio', '-l', 'en', '-norm']

        self.meteor_p = subprocess.Popen(' '.join(self.meteor_cmd),
                                         shell=True,
                                         bufsize=1,
                                         cwd=os.path.dirname(
                                             os.path.abspath(__file__)),
                                         universal_newlines=True,
                                         stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        # Used to guarantee thread safety
        self.lock = threading.Lock()

    def sanitize(self, sourceString):
        return sourceString.replace('\n', '')

    def score(self, hypothesis_str, reference_list):
        self.lock.acquire()

        # Clean the stdio
        self.meteor_p.stdin.flush()

        # SCORE ||| reference 1 words ||| reference n words ||| hypothesis words
        hypothesis_str = hypothesis_str.replace('|||', '').replace('  ', ' ')
        score_line = ' ||| '.join(
            ('SCORE', ' ||| '.join(reference_list), hypothesis_str))

        score_line = self.sanitize(score_line)
        self.meteor_p.stdin.write('{}\n'.format(score_line))
        self.meteor_p.stdin.flush()  # Needed to work with both python2 & 3

        stats = self.meteor_p.stdout.readline().strip()

        eval_line = 'EVAL ||| {}'.format(stats)
        eval_line = self.sanitize(eval_line)
        # EVAL ||| stats
        self.meteor_p.stdin.write('{}\n'.format(eval_line))
        self.meteor_p.stdin.flush()  # Needed to work with both python2 &  3

        score = float(self.meteor_p.stdout.readline().strip())

        self.lock.release()

        return score

    def __del__(self):
        self.lock.acquire()
        self.meteor_p.stdin.close()
        self.meteor_p.kill()
        self.meteor_p.wait()
        self.lock.release()
