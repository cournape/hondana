from setuptools import setup


setup(
    name="hondana",
    version="0.0.1.dev0",
    install_requires=["attrs", "flask", "pyyaml", "six"],
    packages=["hondana", "hondana.templates"],
    package_data={"hondana.templates": ["*.html"]},
    include_package_data=True,
)
