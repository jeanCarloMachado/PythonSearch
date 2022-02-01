import setuptools

setuptools.setup(
    name="python-search",
    version="0.07",
    author="Jean Carlo Machado",
    author_email="machado.c.jean@gmail.com",
    description="Search over python dictionaries",
    long_description="",
    install_requires=[
        "redis",
        "fire",
    ],
    long_description_content_type="text/markdown",
    url="https://github.com/jeanCarloMachado/search_run",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)
