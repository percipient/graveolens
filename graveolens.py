import uuid

try:
    from unittest import mock
except ImportError:
    import mock

from celery.app.task import Task
from celery.result import AsyncResult

__all__ = ['AsyncResultMock', 'CeleryMock']

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

    def __init__(self, assert_all_tasks_called=True, application=None):
        self.assert_all_tasks_called = assert_all_tasks_called
        self.application = application
        self._calls = []
        self._patcher = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    def start(self):
        """Patch the Celery app to intercept calls to Tasks."""
        # If an application was given, patch that instead of the base-class.
        if self.application:
            self._patcher = mock.patch.object(self.application,
                                              'send_task',
                                              new=self._send_task)
        else:
            self._patcher = mock.patch('celery.app.base.Celery.send_task',
                                       new=self._send_task)
        self._patcher.start()

    def stop(self):
        self._patcher.stop()
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

        else:
            return None
