from setuptools import setup, find_packages

setup(
    name="docai-scanner",
    version="0.1.0",
    description="DocAI API scanner for CI pipelines",
    author="DocAI",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0"
    ],
    entry_points={
        "console_scripts": [
            "docai-scan=docai.cli:main"
        ]
    },
    python_requires=">=3.8",
)