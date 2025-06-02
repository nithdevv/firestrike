from setuptools import setup, find_packages
import io

with io.open("README.md", encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="firestrike",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "cryptography>=3.4.7",
        "aiohttp>=3.8.1"
    ],
    entry_points={
        "console_scripts": [
            "firestrike=firestrikew.cli:main_cli",
        ],
    },
    author="FireStrike Team",
    description="Decentralized P2P file sharing network",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="dht p2p file-sharing encryption",
    url="https://github.com/yourusername/firestrike",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Security :: Cryptography",
        "Topic :: Internet :: File Transfer Protocol (FTP)",
        "Programming Language :: Python :: 3.7",
    ],
    python_requires=">=3.7",
    package_data={
        'firestrike': ['firestrike_data/*']
    },
    include_package_data=True
) 