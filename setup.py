from setuptools import setup, find_packages
import os

# Read README safely — never let this break installation
long_description = "Multi-agent AI debates in your terminal - powered by Claude"
readme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")
try:
    with open(readme_path, encoding="utf-8") as f:
        long_description = f.read()
except Exception:
    pass

setup(
    name="agora-debate",
    version="0.2.1",
    description="Multi-agent AI debates in your terminal - powered by Claude",
    long_description=long_description,
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
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
