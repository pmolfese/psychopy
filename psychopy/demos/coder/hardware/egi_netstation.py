#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demonstrate sending EGI Net Station events from PsychoPy.

This example uses egi-pynetstation, which sends ECI commands and event markers
to Net Station / Amp Server Pro with NTP-based event timing. Event delivery is
non-blocking, and drift correction and background drift sampling are enabled by
default.
"""

from psychopy import core, visual

from egi_pynetstation import NetStation


# Change these addresses for your EGI network.
IP_ns = '10.10.10.42'   # computer running Net Station
port_ns = 55513         # ECI TCP port configured in Net Station
IP_amp = '10.10.10.51'  # amplifier / Net Station NTP server


ns = NetStation(IP_ns, port_ns)
ns.connect(ntp_ip=IP_amp)

win = visual.Window(fullscr=True, screen=0, color='black', units='height')
fixation = visual.TextStim(win, text='+', color='white', height=0.08)

recording_started = False
try:
    ns.begin_rec()
    recording_started = True

    ns.send_event(event_type='STRT', label='recording start', start=0.0)

    for trial in range(10):
        # Draw first, then mark the flip that makes the stimulus visible.
        # send_event() captures the timestamp immediately and returns while
        # a package-owned thread performs the network write.
        fixation.draw()
        win.callOnFlip(
            ns.send_event,
            event_type='stim',
            label='stimulus',
            data={'trl_': trial, 'cond': 'demo'},
        )
        win.flip()
        core.wait(0.5)

        # No sampling call is needed here: background drift sampling is the
        # default. Pass auto_drift_background=False to connect() only when an
        # experiment must control exactly when NTP queries occur.
        win.flip()
        core.wait(1.0)

    print('Drift estimate:', ns.drift_estimate())

    # Asynchronous send failures are collected instead of being raised in
    # timing-sensitive experiment code.
    errors = ns.event_errors()
    if errors:
        print(f'WARNING: {len(errors)} events failed to send:', errors[:3])
finally:
    if recording_started:
        ns.end_rec()  # flushes any events still queued
    ns.disconnect()
    win.close()


# The contents of this file are in the public domain.
