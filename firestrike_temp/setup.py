from setuptools import setup, find_packages

setup(
    name="firestrike",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "cryptography>=3.4.7",
        "stem>=1.8.0",
        "pysocks>=1.7.1",
        "aiohttp>=3.8.1"
    ],
    entry_points={
        'console_scripts': [
            'firestrike=firestrikew.cli:main_cli',
        ],
    },
    author="FireStrike Team",
    description="Decentralized anonymous file sharing network through TOR",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="tor dht anonymous file-sharing encryption",
    url="https://github.com/yourusername/firestrike",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Security :: Cryptography",
        "Topic :: Internet :: File Transfer Protocol (FTP)",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires=">=3.8",
) 