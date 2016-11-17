Graveolens
##########

The missing test library for the `Celery`_ Python library. Some of the things graveolens can help with include:

* Provide resultss to Celery task calls without hitting your broker.
* Ensuring that you know exactly which tasks are called.
* Easily assert the arguments of task calls.
* Easily handle results when using ``send_task`` in Celery.

.. _Celery: http://www.celeryproject.org/

The binomial name for celery is `Apium graveolens`_.

.. _Apium graveolens: https://en.wikipedia.org/wiki/Celery

Returning Results
=================

.. code-block:: python

    from my_app.celery import app
    import graveolens

    def test_my_task():
        with graveolens.activate() as celery:
            celery.add('my_app.task', {'done': True, 'status': 'OK'})

            result = app.send_task('my_app.task', 'test', id=3)

            # The result is an EagerResult from Celery.
            assert result.get() == {'done': True, 'status': 'OK'}

            # You can also check ALL the calls that Celery received.
            assert len(celery.calls) == 1
            assert celery.calls[0].name == 'http://twitter.com/api/1/foobar'
            assert celery.calls[0].args == ('test', )
            assert celery.calls[0].kwargs == {'id': 3}

Asserting Celery Calls
======================

By default, if a result is added and unused this raises an ``AssertionError``
when the context manager exits, e.g.:

.. code-block:: python

    import graveolens

    def test_my_task():
        with graveolens.activate() as celery:
            celery.add('my_app.task')

        # Assertion will be raised here because 'my_app.task' is never called.

This can be configured using the ``assert_all_tasks_called`` flag to
``activate()``.

Additionally, if a Celery task is called without having a result set-up then
``graveolens.NotMockedTask`` will be raised.

.. code-block:: python

    from my_app.celery import app
    import graveolens

    def test_my_task():
        with graveolens.activate() as celery:
            try:
                result = app.send_task('my_app.task', 'test', id=3)
            except graveolens.NotMockedTask:
                # Exception will be raised since my_app.task has no result.
                pass
