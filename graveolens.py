from collections import namedtuple
import uuid

try:
    from unittest import mock
except ImportError:
    import mock

from celery.app.task import Task
from celery.result import EagerResult
from celery import states

__all__ = ['AsyncResultMock', 'activate' 'NotMockedTask']


class NotMockedTask(Exception):
    """This task doesn't have a configured result."""


Call = namedtuple('Call', ['name', 'args', 'kwargs'])


class CeleryMock(object):
    """
    Patches a Celery application to hard-code results for celery tasks.

    """

    # TODO Add a flag for asserting on adding an unknown tasks.
    # TODO Add a flag for asserting on calling an unknown task. (vs... calling the actual task?)
    def __init__(self, assert_all_tasks_called=True, app=None):
        self.assert_all_tasks_called = assert_all_tasks_called
        self._app = app

        # Actual Celery calls that were intercepted.
        self.calls = []
        # The set of configured results to send back to task calls.
        self._results = []
        # Modifications to Celery.
        self._patches = []

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    def start(self):
        """Patch the Celery app to intercept calls to Tasks."""
        # If an application was given, patch that instead of the base-class.
        if self._app:
            self._patches.append(mock.patch.object(self._app, 'send_task',
                                                   new=self._send_task))
        else:
            self._patches.append(mock.patch('celery.app.base.Celery.send_task',
                                            new=self._send_task))

        # Also capture apply, note that apply_async just ends up calling
        # send_task on the app.
        self._patches.append(
            mock.patch('celery.app.task.Task.apply', new=self._get_apply()))
        # Also capture a direct call of the task.
        self._patches.append(
            mock.patch('celery.app.task.Task.__call__', new=self._get_apply()))

        # Actually turn on the patches.
        for patch in self._patches:
            patch.start()

    def stop(self):
        # Shut off all the patches.
        for patch in self._patches:
            patch.stop()

        if self.assert_all_tasks_called and self._results:
            raise AssertionError(
                'Not all tasks have been called {}'.format(self._results))

    def add(self, task, result, state=states.SUCCESS):
        """
        task can be either a task name or a task object.

        """
        if isinstance(task, Task):
            task_name = task.name
        elif isinstance(task, (str, unicode)):
            task_name = str(task)

        # TODO Ensure that the task exists in a celery app using app.

        # Generate an AsyncResult for the result.
        result = EagerResult(uuid.uuid4(), result, state)

        self._results.append((task_name, result))

    def _send_task(self, name, args=None, kwargs=None):
        """
        The magic, lookup the task name, and return the result!

        TODO: Use args/kwargs in here.

        """
        # Track that this task was called. Normalize the input to be empty
        # tuples/dicts instead of sometimes None.
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        self.calls.append(Call(name, args, kwargs))

        # Find the first instance of this task name.
        for i, (task_name, result) in enumerate(self._results):
            if name == task_name:
                # Don't re-use this result.
                self._results.pop(i)
                return result

        # TODO If the task has ignore_result on, handle that.

        # The task wasn't found, so no result is known. Raise an exception.
        # TODO Can we behave more like Celery here?
        raise NotMockedTask("No result available for task: %s" % name)

    def _get_apply(self):
        mock = self
        def _apply(self, args=None, kwargs=None, link=None, link_error=None, **options):
            return mock._send_task(self.name, args=args, kwargs=kwargs)

        return _apply


def activate(*args, **kwargs):
    """Give control of Celery to graveolens. Used as a context manager."""
    return CeleryMock(*args, **kwargs)
