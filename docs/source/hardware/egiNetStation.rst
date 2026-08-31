.. _egi:

Sending triggers via EGI NetStation
===================================

The `egi-pynetstation
<https://egi-pynetstation.readthedocs.io/en/latest/>`_ package sends ECI event
markers from |PsychoPy| to EGI Net Station or Amp Server Pro. Event timestamps
are captured immediately, while network communication runs in the background.

Install
-------

Install ``egi-pynetstation`` into the same Python environment that runs
|PsychoPy|. Standalone users can use ``Tools > Plugin/packages manager...``,
or install from that environment's terminal:

.. code-block:: bash

    python -m pip install egi-pynetstation

Restart |PsychoPy| after installation.

The five commands
-----------------

Most experiments need only this lifecycle:

.. code-block:: python

    from egi_pynetstation import NetStation

    eci_client = NetStation('10.10.10.42', 55513)
    eci_client.connect(ntp_ip='10.10.10.51')
    eci_client.begin_rec()
    eci_client.send_event(event_type='stim')
    eci_client.end_rec()
    eci_client.disconnect()

The example addresses are common on EGI 400-series systems, but the Net
Station address, NTP address, and ECI port can differ between labs. Confirm
them with the person who maintains the acquisition system.

Drift correction and background NTP sampling start automatically. Do not add
periodic clock-sync or NTP-sampling calls to the trial loop.

Use in Builder
--------------

Add a Code Component near the beginning of the experiment.

.. figure:: /images/insertCode.png

    Select the Code Component from the Custom component drop-down.

In **Begin Experiment**, connect and start the recording:

.. code-block:: python

    from egi_pynetstation import NetStation

    eci_client = NetStation('10.10.10.42', 55513)
    eci_client.connect(ntp_ip='10.10.10.51')
    eci_client.begin_rec()

Mark a visual onset
-------------------

In **Begin Routine**, reset a flag:

.. code-block:: python

    triggerSent = False

In **Each Frame**, schedule the marker on the flip that first presents the
stimulus. Replace ``stimulus`` with the name of the relevant Builder
Component:

.. code-block:: python

    if stimulus.status == STARTED and not triggerSent:
        win.callOnFlip(
            eci_client.send_event,
            event_type='stim',
            label='stimulus',
        )
        triggerSent = True

``event_type`` must be exactly four ASCII characters. Optional ``data`` keys
must also be exactly four characters:

.. code-block:: python

    win.callOnFlip(
        eci_client.send_event,
        event_type='stim',
        data={'trl_': trials.thisN, 'cond': 'target'},
    )

Call ``send_event()`` directly for events that are not tied to a display
refresh, such as responses. Do not use ``wait=True`` inside
``win.callOnFlip()``.

Stop cleanly
------------

In **End Experiment**, stop the recording, check its health, and disconnect:

.. code-block:: python

    eci_client.end_rec()

    summary = eci_client.session_summary()
    if not summary['ok']:
        print('EGI session warning:', summary)

    eci_client.disconnect()

Validate the timing
-------------------

Run the clock check once on every stimulus computer:

.. code-block:: bash

    python -m egi_pynetstation.check_clocks

Its final line should say that the clocks are suitable for drift-corrected ECI
timing. Before collecting data, also run the package's Example 5 timing test
with a photocell on the actual display and computers used by the experiment.

If that test shows startup drift, either allow more time between
``connect()`` and ``begin_rec()``, or enable the short warmup model:

.. code-block:: python

    eci_client.connect(ntp_ip='10.10.10.51', drift_warmup=True)

See the `Timing Test
<https://egi-pynetstation.readthedocs.io/en/latest/timing_test.html>`_ for the
Example 5 command and interpretation guidance.

More information
----------------

The `egi-pynetstation documentation
<https://egi-pynetstation.readthedocs.io/en/latest/>`_ covers installation,
multiple recordings per connection, timing validation, drift behavior, and
diagnostics. Source code and issue reporting are available from the
`egi-pynetstation GitHub project
<https://github.com/nimh-sfim/egi-pynetstation>`_.

For help with the |PsychoPy| experiment itself, use the
`PsychoPy Forum <https://discourse.psychopy.org/>`_.
