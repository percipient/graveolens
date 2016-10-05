import unittest

import celery

import graveolens

app = celery.Celery('graveolens')
#app.config_from_object('graveolens.settings', force=True)



class TestGraveolens(unittest.TestCase):
    def test_result(self):
        with graveolens.CeleryMock() as mock:
            mock.add('foo.bar', 'FOOBAR!')

            result = app.send_task('foo.bar')

            self.assertIsInstance(result, graveolens.AsyncResultMock)
            self.assertEqual(result.get(), 'FOOBAR!')

    def test_subclass_app(self):
        with graveolens.CeleryMock(application=app) as mock:
            mock.add('foo.bar', 'FOOBAR!')

            result = app.send_task('foo.bar')

            self.assertIsInstance(result, graveolens.AsyncResultMock)
            self.assertEqual(result.get(), 'FOOBAR!')

    def test_non_existant_task(self):
        pass


if __name__ == '__main__':
    unittest.main()
