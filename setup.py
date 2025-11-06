"""Setup script for LevelUp Bot."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="levelup-bot",
    version="1.0.0",
    author="LevelUp Bot",
    description="A Telegram bot for automated messaging and challenge solving",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/levelup_bot",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.11",
    install_requires=[
        "pillow==12.0.0",
        "pix2text==1.1.4",
        "python-dotenv==1.2.1",
        "requests==2.32.5",
        "Telethon==1.42.0",
    ],
    entry_points={
        "console_scripts": [
            "levelup-bot=levelup_bot.main:main",
        ],
    },
)

