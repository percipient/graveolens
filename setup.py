import codecs

from setuptools import setup


def long_description():
    with codecs.open('README.rst', encoding='utf8') as f:
        return f.read()

setup(
    name='graveolens',
    py_modules=['graveolens'],
    version='0.1.2',
    description='The missing test library for Celery.',
    long_description=long_description(),
    url='https://github.com/percipient/graveolens',
    download_url='https://github.com/percipient/graveolens',
    author='Percipient Networks, LLC',
    author_email='support@strongarm.io',
    license='Apache 2.0',
    install_requires=[
        # Not yet tested with Celery 4.
        'celery>3<4a',
        'mock>=2.0.0',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Networking',
    ],
)
