from setuptools import setup


def long_description():
    from os import path

    this_directory = path.abspath(path.dirname(__file__))
    with open(path.join(this_directory, "README.md")) as readme_f:
        contents = readme_f.read()
        return contents


setup(
    name="atakama_policy_basics",
    version="1.0.2",
    description="Convert python docstring documentation to github markdown files",
    packages=["policy_basics"],
    url="https://github.com/AtakamaLLC/policy_basics",
    long_description=long_description(),
    long_description_content_type="text/markdown",
    setup_requires=["wheel"],
    entry_points={
        "console_scripts": ["policy_basics=policy_basics.__main__:main"],
    },
)
