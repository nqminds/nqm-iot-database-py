import nqm.iotdatabase
import tomlkit


def test_version():
    """Test that the version in pyproject.toml matches the __version__"""
    with open("./pyproject.toml", "r") as tomlfile:
        contents = tomlfile.read()
        parsed_contents = tomlkit.parse(contents)
    loaded_version = parsed_contents["tool"]["poetry"]["version"]
    assert nqm.iotdatabase.__version__ == loaded_version
