import unittest

import celery

import graveolens

app = celery.Celery('graveolens')
# Attempt to not use a broker.
app.conf.update(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    # But if we do hit the broker, for some reason, then timeout fast!
    BROKER_CONNECTION_TIMEOUT=0,
    BROKER_CONNECTION_RETRY=False,
)

class TestException(Exception):
    """An exception used in tests."""

@app.task
def raising_task():
    raise TestException("Task shouldn't be called.")


class TestCelery(unittest.TestCase):
    """Ensure that Celery is actually configured in a sane-ish way."""

    def test_name(self):
        """Ensure we know the proper name of the task."""
        self.assertEqual(raising_task.name, 'graveolens.raising_task')

    def test_call(self):
        """Direct call skips celery."""
        with self.assertRaises(TestException):
            raising_task()

    def test_delay(self):
        """Delay is eager so resolves instantly."""
        with self.assertRaises(TestException):
            raising_task.delay()

    def test_apply(self):
        """Apply skips celery."""
        with self.assertRaises(TestException):
            raising_task.apply()

    def test_apply_async(self):
        """Apply async is eager so resolves instantly."""
        with self.assertRaises(TestException):
            raising_task.apply_async()

    # TODO The following doesn't work. We could create another decorator in
    #      graveolens that replaces send_task with direct look-ups. This works
    #      well and is nice.
    # See https://github.com/celery/celery/issues/581
    @unittest.skip("Always eager doesn't effect send_task.")
    def test_send_task(self):
        """Send task is eager so resolves instantly."""
        with self.assertRaises(TestException):
            app.send_task('graveolens.raising_task')

    @unittest.skip("Always eager doesn't effect send_task.")
    def test_non_existant_send_task(self):
        """Send task for a non-existant task raises a NotRegistered exception."""
        app.send_task('foo.bar')


class TestGraveolens(unittest.TestCase):
    """Ensure that graveolens intercepts calls and returns the expected results."""

    def assertResult(self, mock, result, args=(), kwargs={}, argsrepr=None, kwargsrepr=None):
        """Ensure that the mock and result are in the expected states."""
        # Check that the result is as expected.
        self.assertIsInstance(result, celery.result.EagerResult)
        self.assertEqual(result.state, celery.states.SUCCESS)
        self.assertEqual(result.get(), 'foobar')

        # Test that the task call was stored properly.
        self.assertIsInstance(mock.calls[0], graveolens.Call)
        self.assertEqual(mock.calls[0], ('graveolens.raising_task', args, kwargs, argsrepr, kwargsrepr))

    def test_call(self):
        """Direct call skips celery return a mocked value."""
        with graveolens.activate() as mock:
            mock.add('graveolens.raising_task', 'foobar')
            result = raising_task()
            self.assertResult(mock, result)

    def test_delay(self):
        """Delay returns a mocked value."""
        with graveolens.activate() as mock:
            mock.add('graveolens.raising_task', 'foobar')
            result = raising_task.delay()
            self.assertResult(mock, result)

    def test_apply(self):
        """Apply returns a mocked value."""
        with graveolens.activate() as mock:
            mock.add('graveolens.raising_task', 'foobar')
            result = raising_task.apply()
            self.assertResult(mock, result)

    def test_apply_async(self):
        """Apply async returns a mocked value."""
        with graveolens.activate() as mock:
            mock.add('graveolens.raising_task', 'foobar')
            result = raising_task.apply_async()
            self.assertResult(mock, result)

    def test_send_task(self):
        """Send task returns a mocked value."""
        with graveolens.activate() as mock:
            mock.add('graveolens.raising_task', 'foobar')
            result = app.send_task('graveolens.raising_task')
            self.assertResult(mock, result)

    def test_send_task_args(self):
        """Send task returns a mocked value."""
        with graveolens.activate() as mock:
            mock.add('graveolens.raising_task', 'foobar')
            result = app.send_task('graveolens.raising_task', args=('test',))
            self.assertResult(mock, result, args=('test',))

    def test_send_task_kwargs(self):
        """Send task returns a mocked value."""
        with graveolens.activate() as mock:
            mock.add('graveolens.raising_task', 'foobar')
            result = app.send_task('graveolens.raising_task', kwargs={'test': True})
            self.assertResult(mock, result, kwargs={'test': True})


    def test_send_task_argsrepr(self):
        """Send task returns a mocked value."""
        with graveolens.activate() as mock:
            mock.add('graveolens.raising_task', 'foobar')
            result = app.send_task('graveolens.raising_task', args=('test',), argsrepr='test')
            self.assertResult(mock, result, args=('test',), argsrepr='test')

    def test_send_task_kwargsrepr(self):
        """Send task returns a mocked value."""
        with graveolens.activate() as mock:
            mock.add('graveolens.raising_task', 'foobar')
            result = app.send_task('graveolens.raising_task', kwargs={'test': True}, kwargsrepr='test')
            self.assertResult(mock, result, kwargs={'test': True}, kwargsrepr='test')


    def test_non_existant_send_task(self):
        """Send task for a value that was not configured raises an exception."""
        with graveolens.activate() as mock:
            with self.assertRaises(graveolens.NotMockedTask):
                result = app.send_task('foo.bar')

    @unittest.skip("Checking for tasks in the registry isn't supported yet.")
    def test_non_existant_add(self):
        """Trying to return a value for a non-existant task should raise."""
        with graveolens.activate() as mock:
            with self.assertRaises(celery.exceptions.NotRegistered):
                mock.add('foo.bar', 'foobar')

    def test_add_task(self):
        """Adding a task should work like a task name."""
        with graveolens.activate() as mock:
            mock.add(raising_task, 'foobar')
            result = app.send_task('graveolens.raising_task')
            self.assertResult(mock, result)

    def test_unused_add(self):
        """Not using all added results should raise."""
        with self.assertRaises(AssertionError):
            with graveolens.activate() as mock:
                # Unused add.
                mock.add('graveolens.raising_task', 'foobar')

    def test_unused_add_no_exceptions(self):
        """Not using all added results doesn't raise if not configured to."""
        with graveolens.activate(assert_all_tasks_called=False) as mock:
            mock.add('graveolens.raising_task', 'foobar')

        # Should still be calls in the buffer.
        self.assertEqual(len(mock._results), 1)

    def test_unused_add_exception_pass_thru(self):
        """
        Exceptions raised in the context manager should pass through instead of
        being shadowed by the exception from not using all results.
        """
        with self.assertRaises(TestException):
            with graveolens.activate() as mock:
                # Unused add.
                mock.add('graveolens.raising_task', 'foobar')

                raise TestException()

    def test_subclass_app(self):
        # TODO Duplicate the above tests with providing a specific app.
        with graveolens.activate(app=app) as mock:
            mock.add('graveolens.raising_task', 'foobar')

            result = app.send_task('graveolens.raising_task')
            self.assertResult(mock, result)


if __name__ == '__main__':
    unittest.main()
