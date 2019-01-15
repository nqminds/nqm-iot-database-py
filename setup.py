from setuptools import setup

setup(
	name='nqm-iot-database-utils-py',
	version='1',
	packages=['nqm.iotdatabase'],
	author='Alois Klink',
	author_email='alois.klink@gmail.com',
	install_requires=['sqlalchemy', 'mongosql', 'shortuuid', 'numpy', 'future']
)
