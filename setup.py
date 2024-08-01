from setuptools import setup, find_packages

setup(
    name="tv_schedule",
    version="0.1.0",
    description="A TV schedule application",
    author="araki777",
    author_email="arakichi777@icloud.com",
    packages=find_packages(),
    install_requires=[
      "bs4==0.0.1",
      "requests==2.31.0",
      "python-dotenv==1.0.0",
      "selenium==4.11.2",
      "azure-functions==1.20.0",
    ],
    python_requires='>=3.10',
)