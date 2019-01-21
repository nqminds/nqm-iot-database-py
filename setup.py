from setuptools import setup

setup(
    name='nqm-iot-database-py',
    version=PipMethods.find_version("nqm", "iotdatabase", "__init__.py"),
    packages=['nqm.iotdatabase'],
    author='Alois Klink',
    author_email='alois.klink@gmail.com',
    install_requires=['sqlalchemy', 'mongosql', 'shortuuid', 'numpy', 'future']
)
