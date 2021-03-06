from distutils.core import setup

setup(
    name='mountwizzard',
    version='2.0.8',
    packages=[
        'mountwizzard',
        'mountwizzard/support'
    ],
    install_requires=[
        'PyQt5>=5.6',
        'matplotlib>=1.5.3',
        'pypiwin32>=219',
        'pyfits>=3.4'
    ],
    url='https://pypi.python.org/pypi/mountwizzard',
    license='APL 2.0',
    author='mw',
    author_email='michael@wuertenberger.org',
    description='tooling for a 10micron mount',
)
