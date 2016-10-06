import uuid

try:
    from unittest import mock
except ImportError:
    import mock

from celery.app.task import Task
from celery.result import AsyncResult

__all__ = ['AsyncResultMock', 'CeleryMock' 'NotMockedTask']


class NotMockedTask(Exception):
    """This task doesn't have a configured result."""


class AsyncResultMock(AsyncResult):
    def __init__(self, result):
        super(AsyncResultMock, self).__init__(id=uuid.uuid4())

        self._result = result

    def get(self, *args, **kwarg):
        return self._result


class CeleryMock(object):
    """
    Patches a Celery application to hard-code results for celery tasks.

    """

    # TODO Add a flag for asserting on adding an unknown tasks.
    # TODO Add a flag for asserting on calling an unknown task. (vs... calling the actual task?)
    def __init__(self, assert_all_tasks_called=True, app=None):
        self.assert_all_tasks_called = assert_all_tasks_called
        self._app = app
        self._calls = []
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

        if self.assert_all_tasks_called and self._calls:
            raise AssertionError(
                'Not all tasks have been called {}'.format(self._calls))

    def add(self, task, result):
        """
        task can be either a task name or a task object.
        result can be a raw value or a 

        """
        if isinstance(task, Task):
            task_name = task.name
        elif isinstance(task, (str, unicode)):
            task_name = str(task)

        # TODO Ensure that the task exists in a celery app using app.

        # Generate an AsyncResult for the result.
        result = AsyncResultMock(result)

        self._calls.append((task_name, result))

    def _send_task(self, name, args=None, kwargs=None):
        """
        The magic, lookup the task name, and return the result!

        TODO: Use args/kwargs in here.

        """
        # Find the first instance of this task name.
        for i, (task_name, result) in enumerate(self._calls):
            if name == task_name:
                # Don't re-use this result.
                self._calls.pop(i)
                return result

        # The task wasn't found, so no result is known. Raise an exception.
        # TODO Can we behave more like Celery here?
        raise NotMockedTask("No result available for task: %s" % name)

    def _get_apply(self):
        mock = self
        def _apply(self, args=None, kwargs=None, link=None, link_error=None, **options):
            return mock._send_task(self.name, args=args, kwargs=kwargs)

        return _apply
