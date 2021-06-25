from setuptools import find_packages, setup

setup(
    name="custom_app",
    version="0.1",
    description="",
    author="Indico",
    author_email="indico@indico.io",
    packages=find_packages(),
    install_requires=[
    ],
    extras_require={
        "test": ["pytest>=6.2.4"]
    },
)
