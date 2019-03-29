from setuptools import setup

# required for gets the current version of the package
import nqm.iotdatabase

setup(
    name='nqm.iotdatabase',
    version=nqm.iotdatabase.__version__,
    packages=['nqm.iotdatabase', 'nqm.iotdatabase.ndarray'],
    author='Alois Klink',
    author_email='alois.klink@gmail.com',
    description="Library for accessing a local nqm-iot-database",
    include_package_data=True,
    python_requires=">=3.6",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/nqminds/nqm-iot-database-py',
    install_requires=['sqlalchemy', 'mongosql>=1.5.1-0', 'shortuuid', 'numpy', 'future'],
    zip_safe=True,
)
