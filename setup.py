from setuptools import setup, find_packages

setup(
    name="agora-debate",
    version="0.2.0",
    description="Multi-agent AI debates in your terminal — powered by Claude",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Bernhard Brugger",
    author_email="bernhardb0100@gmail.com",
    url="https://github.com/bernhardbrugger/agora",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": ["personas/*.yaml"],
    },
    install_requires=[
        "anthropic>=0.40.0",
        "click>=8.0",
        "rich>=13.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0",
    ],
    entry_points={
        "console_scripts": [
            "agora=agora.cli:main",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
