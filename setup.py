import setuptools

with open("README.md", "r") as fh:
  long_description = fh.read()

setuptools.setup(
    name="paperpython",
    version="0.0.3",
    author="SagaraBattousai",
    author_email="jamesafcalo@gmail.com",
    description="A WSGI compatible server aimed to be used with paperServer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SagaraBattousai/paperPython",
    packages=setuptools.find_packages(),
    classifiers=[
      "Programming Language :: Python :: 3",
      "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
      "Operating System :: OS Independent",
      ],
    python_requires='>=3.5',
)
