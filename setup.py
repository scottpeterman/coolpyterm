from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        return f.read()

# Read requirements
def read_requirements():
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, 'requirements.txt'), encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="coolpyterm",
    version="0.1.2",
    author="Scott Peterman",
    author_email="scottpeterman@gmail.com",
    description="A hardware-accelerated SSH terminal emulator with authentic retro CRT effects, inspired by the Cool Retro Terminal project",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/scottpeterman/coolpyterm",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet",
        "Topic :: System :: Networking",
        "Topic :: Terminals",
        "Topic :: Utilities",
    ],
    python_requires=">=3.10",
    install_requires=read_requirements(),
    extras_require={
        "dev": [

        ],
    },
    entry_points={
        "console_scripts": [
            "coolpyterm-con=coolpyterm.cpt:main",
        ],
        "gui_scripts": [
            "coolpyterm=coolpyterm.cpt:main",
        ],
    },
    package_data={
        "coolpyterm": ["logs/*"],
    },
    include_package_data=True,
    zip_safe=False,
)