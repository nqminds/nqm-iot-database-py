import io
from setuptools import setup

setup(
    name="nqm_iot_database",
    version="1.0.0",
    author="Alois Klink",
    author_email="alois.klink@gmail.com",
    packages=["nqm_iot_database"],
    url="https://github.com/nqminds/nqm-iot-database-py",
    description="Python port of nqminds/nqm-iot-database-utils",
    install_requires=["sqlalchemy", "mongosql", "shortuuid"]
)
