import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="polyclash",
    version="0.0.1",
    author="Mingli Yuan",
    author_email="mingli.yuan@gmail.com",
    description="A python 3d spherical Go game on a snub dodecahedron board",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/spherical-go/polyclash",
    project_urls={
        'Documentation': 'https://github.com/spherical-go/polyclash',
        'Source': 'https://github.com/spherical-go/polyclash',
        'Tracker': 'https://github.com/spherical-go/polyclash/issues',
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(
        exclude=['tests', 'model3d', 'scripts', 'bin']
    ),
    python_requires='>=3.10',
    install_requires=[
        'numpy==1.26.4',
        'scipy==1.13.0',
        'PyQt5==5.15.10',
        'pyvista==0.43.7',
        'pyvistaqt==0.11.0',
        'requests==2.31.0',
        'python-socketio[client]==5.11.2',
        'flask==3.0.3',
        'flask-socketio==5.3.6',
        'loguru==0.7.2',
        'redis==5.0.4',
    ],
    test_suite='pytest',
    tests_require=[
        'pytest',
        'pytest-flask',
    ],
    entry_points={
        'console_scripts': [
            'polyclash-client = polyclash.client:main',
            'polyclash-server = polyclash.server:main',
        ],
    },
)
