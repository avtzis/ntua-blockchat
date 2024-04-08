from setuptools import setup

setup(
  name="blockchat",
  version="0.1.0",
  author="Altan Avtzi",
  author_email="avtzialtan@gmail.com",
  description="A simple blockchain network",
  long_description=open("README.md").read(),
  long_description_content_type="text/markdown",
  url="https://github.com/avtzis/ntua-blockchat",
  install_requires=[
    "cffi",
    "cryptography",
    "pycparser",
    "prompt_toolkit"
  ],
  python_requires=">=3.11",
  entry_points={
    "console_scripts": [
      "blockchat=blockchat:main"
    ]
  },
  classifiers=[
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "License :: OSI Approved :: MIT License",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Libraries :: Python Modules",
  ],
  keywords="ntua blockchain crypto distributed-systems",
)
