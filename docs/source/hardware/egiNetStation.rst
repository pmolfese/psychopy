.. _egi:

Sending triggers via EGI NetStation
===================================

The `egi-pynetstation <https://egi-pynetstation.readthedocs.io/en/latest/>`_
package sends Experimental Control Interface (ECI) commands and timestamped
event markers from |PsychoPy| to EGI Net Station or Amp Server Pro. It is
designed for experiments that need to mark a display refresh without making
that refresh wait for a network round trip.

.. warning::

    **egi-pynetstation 2.0 is a breaking release.** Code written for version
    1.x, or for the older ``egi``/``pynetstation`` API, should not be expected
    to work unchanged with version 2.0 or later.

    In 2.0, ``send_event()`` is non-blocking by default, automatic drift
    sampling runs in the background, and a recording uses one fixed ECI clock
    synchronization. Do not carry forward old code that polls Net Station for
    every event, repeatedly calls ``resync()``, or expects ``send_event()`` to
    return an immediate response. Use the 2.0 pattern shown on this page.

Default in 2.0: background drift refresh
----------------------------------------

The recommended setup is also the simplest one. Calling ``connect()`` with an
NTP server enables drift correction and starts the background sampling thread;
there is no refresh or sampling call to add to your trial loop.

.. code-block:: python

    from egi_pynetstation import NetStation

    eci_client = NetStation('10.10.10.42', 55513)
    eci_client.connect(ntp_ip='10.10.10.51')
    eci_client.begin_rec()

Version 2.0 uses two package-owned background workers:

* A **drift sampler** periodically queries the amplifier or Net Station NTP
  server and updates the clock model. The thread starts during ``connect()``
  and begins collecting usable samples after ``begin_rec()`` establishes the
  recording's timestamp epoch.
* An **event sender** writes queued markers to the ECI socket. ``send_event()``
  captures the timestamp on the calling thread and returns immediately, so it
  is safe to schedule with ``win.callOnFlip()``.

The NTP refresh does **not** send another ECI ``NTPClockSync`` command, reset
the event epoch, or create an event marker. One ECI synchronization at
``begin_rec()`` establishes the epoch; background NTP queries measure and
correct the gradual drift after that.

.. important::

    For the normal setup, leave ``auto_drift_background`` at its default of
    ``True``. Do not add ``sample_drift()``, ``sample_drift_if_due()``, or
    repeated ``resync()`` calls to the trial loop. Manual sampling is an
    advanced opt-in described near the end of this page.

Step one: verify the EGI network and NTP server
-----------------------------------------------

Confirm the addresses used by your acquisition setup before writing the
experiment. A common 400-series configuration is:

* Net Station computer and ECI server: ``10.10.10.42``
* amplifier and NTP server: ``10.10.10.51``
* ECI port configured in Net Station: ``55513``

The exact addresses vary by laboratory. With some 300-series configurations,
the Net Station computer supplies NTP instead of the amplifier. Check the
vendor configuration or ask the person who maintains the acquisition system
rather than assuming the example addresses are correct.

On macOS or Linux, an NTP server can be checked from a terminal with, for
example:

.. code-block:: bash

    sntp -d 10.10.10.51

The amplifier's web interface may also show the amplifier and Net Station
addresses.

.. figure:: /images/egi-netstation.png

    Example EGI network information showing an amplifier at ``10.10.10.51``
    and Net Station at ``10.10.10.42``.

Step two: install egi-pynetstation 2.0
--------------------------------------

Recent standalone |PsychoPy| versions can install the package from
``Tools > Plugin/packages manager...``. Open the **Packages** tab, search for
``egi-pynetstation``, and install version 2.0 or later. Restart |PsychoPy|
after installation.

Alternatively, install it into the same Python environment that runs
|PsychoPy|:

.. code-block:: bash

    python -m pip install "egi-pynetstation>=2"

For a standalone Windows installation, use the ``python.exe`` inside the
|PsychoPy| installation, for example:

.. code-block:: bat

    "C:\Program Files\PsychoPy\python.exe" -m pip install "egi-pynetstation>=2"

egi-pynetstation 2.0 requires Python 3.9 or later. Verify that |PsychoPy| is
loading the expected release before running a study:

.. code-block:: python

    from importlib.metadata import version
    print(version('egi-pynetstation'))

Check the stimulus computer's clocks once after installing the package and
again after major Python, operating-system, or hardware changes:

.. code-block:: bash

    python -m egi_pynetstation.check_clocks

This command reports the measured resolution of ``time.time()`` and
``time.monotonic()``, sleep overshoot, and clock-difference jitter. On Windows,
Python 3.13 or later is strongly recommended.

Step three: add the connection to a Builder experiment
------------------------------------------------------

Add a Code Component to an instructions or setup Routine near the beginning
of the experiment.

.. figure:: /images/insertCode.png

    Select the Code Component from the Custom component drop-down.

In the **Begin Experiment** tab, import the package, connect, and start the
recording. Change the addresses and port for your EGI network:

.. code-block:: python

    from egi_pynetstation import NetStation

    # Computer running Net Station and the ECI port configured there.
    IP_ns = '10.10.10.42'
    port_ns = 55513

    # Amplifier or Net Station host providing NTP.
    IP_amp = '10.10.10.51'

    eci_client = NetStation(IP_ns, port_ns)
    eci_client.connect(ntp_ip=IP_amp)  # background drift refresh is automatic
    eci_client.begin_rec()             # the one ECI clock sync for this run
    eci_client.send_event(event_type='STRT', start=0.0)

``begin_rec()`` should be called exactly once for a recording. Do not add a
periodic ``resync()`` call: resetting the ECI epoch during a recording creates
a timestamp discontinuity and is refused by the 2.0 API.

Step four: mark the screen refresh
----------------------------------

In the **Begin Routine** tab of a Code Component in the trial Routine, reset a
flag so that the marker is scheduled only once:

.. code-block:: python

    triggerSent = False

In the **Each Frame** tab, schedule the marker on the flip that first presents
the stimulus. Change ``stimulus`` to the name of the relevant Builder
Component:

.. code-block:: python

    if stimulus.status == STARTED and not triggerSent:
        win.callOnFlip(
            eci_client.send_event,
            event_type='stim',
            label='stimulus',
        )
        triggerSent = True

The event is timestamped inside the flip callback, before the network write.
The background event sender then transmits it without holding up the following
frame.

.. note::

    ``event_type`` must be **exactly four ASCII characters**, not merely four
    or fewer. Keys in an optional ``data`` dictionary must also be exactly
    four characters. For example:

    .. code-block:: python

        win.callOnFlip(
            eci_client.send_event,
            event_type='stim',
            label='target onset',
            data={'trl_': trials.thisN, 'cond': 'target'},
        )

Call ``send_event()`` directly for an event that is not tied to a visual
refresh, such as a response:

.. code-block:: python

    eci_client.send_event(event_type='resp', desc=f'key={key_resp.keys}')

Both calls are non-blocking. The difference is the moment being marked: the
flip callback marks the display refresh, while a direct call marks that line
of experiment code.

Step five: stop cleanly and inspect the session
-----------------------------------------------

In the **End Experiment** tab of a Code Component, stop the recording and
disconnect:

.. code-block:: python

    eci_client.end_rec()       # flushes queued events before stopping

    summary = eci_client.session_summary()
    if not summary['ok']:
        print('EGI session warning:', summary)

    eci_client.disconnect()    # stops both background workers

``end_rec()`` and ``disconnect()`` both flush queued markers. Keep the
explicit calls so that a normal experiment shutdown is orderly and any error
can be reported immediately.

Optional advanced features
--------------------------

Most experiments should stop reading here and use the defaults above. The
following controls are for diagnostics or experiments with a specific reason
to take over part of the timing machinery.

Manual drift sampling
^^^^^^^^^^^^^^^^^^^^^

To guarantee that NTP queries occur only during known quiet periods, disable
the background sampler explicitly:

.. code-block:: python

    eci_client.connect(
        ntp_ip=IP_amp,
        auto_drift_background=False,
        auto_drift_interval=15.0,
        auto_drift_min_pause=0.35,
    )

Then call ``sample_drift_if_due()`` during an inter-trial interval or other
safe pause:

.. code-block:: python

    eci_client.sample_drift_if_due(available_pause=iti_remaining)

.. warning::

    After setting ``auto_drift_background=False``, the experiment is
    responsible for sampling. If it never calls ``sample_drift_if_due()`` or
    ``sample_drift()``, the drift model receives no data and correction never
    engages. Never call either sampling method from ``win.callOnFlip()``;
    an NTP sample performs several network queries and blocks the calling
    thread.

Synchronous event responses
^^^^^^^^^^^^^^^^^^^^^^^^^^^

``send_event()`` returns ``None`` by default because transmission happens on
the background worker. A diagnostic tool that truly needs the amplifier's
response can opt into a blocking call:

.. code-block:: python

    response = eci_client.send_event(event_type='test', wait=True)

Do not use ``wait=True`` inside ``win.callOnFlip()`` or a timing-sensitive
frame loop.

Error logging and runtime diagnostics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pass an error-log path when constructing the client to retain structured
JSON-lines diagnostics:

.. code-block:: python

    eci_client = NetStation(
        IP_ns,
        port_ns,
        error_log='data/egi_errors.jsonl',
    )

Useful runtime checks include:

.. code-block:: python

    print(eci_client.drift_estimate())
    print(eci_client.clock_state())
    print(eci_client.session_summary())
    print(eci_client.event_errors())  # asynchronous send failures
    print(eci_client.eci_errors())    # rejected or malformed ECI responses

Use these between trials or at the end of a run, not inside a flip callback.
``flush_events()`` is also available if an experiment needs an explicit
mid-run synchronization point.

Testing the integration
-----------------------

Before using the integration in a real study:

* Build a short experiment with only a few visual markers.
* Confirm that the expected four-character event codes appear in Net Station.
* Check ``session_summary()``, ``event_errors()``, and ``eci_errors()``.
* Validate stimulus-to-marker timing with a photodiode or photocell.
* Run the clock diagnostic on the actual stimulus computer, not on a general
  development machine or virtual machine.

.. figure:: /images/serialExp.png

    A small test experiment is easier to diagnose than the full study.

Getting help
------------

For problems with the |PsychoPy| experiment, post details on the
`PsychoPy Forum <https://discourse.psychopy.org/>`_. Include the operating
system, Python and |PsychoPy| versions, egi-pynetstation version, amplifier
series, and any output from ``check_clocks`` or ``session_summary()``.

For package behavior and the complete drift-model reference, see the
`egi-pynetstation documentation
<https://egi-pynetstation.readthedocs.io/en/latest/>`_ and
`GitHub project <https://github.com/nimh-sfim/egi-pynetstation>`_.
