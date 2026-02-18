from setuptools import setup, find_packages

setup(
    name="agora-debate",
    version="0.1.0",
    description="CLI framework for multi-agent debates powered by Claude",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Bernhard Brugger",
    packages=find_packages(),
    include_package_data=True,
    package_data={"": ["personas/*.yaml"]},
    data_files=[("personas", [
        "personas/neutral.yaml",
        "personas/investor_panel.yaml",
        "personas/startup_team.yaml",
        "personas/philosophy.yaml",
        "personas/devils_advocate.yaml",
    ])],
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
)
