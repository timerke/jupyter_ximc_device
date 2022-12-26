from setuptools import find_packages, setup


setup(name="ximc_device",
      version="0.1.0",
      description="Simple library to work with XIMC controllers",
      long_description=open("README.md", "r", encoding="utf-8").read(),
      long_description_content_type="text/markdown",
      url="https://github.com/timerke/ximc_device",
      author="timerke",
      author_email="timerke@mail.ru",
      packages=find_packages(),
      install_requires=[
          "ipympl",
          "libximc",
          "matplotlib",
      ],
      python_requires=">=3.6")
