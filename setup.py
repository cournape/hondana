from setuptools import setup


setup(
    name="hondana",
    version="0.0.1.dev0",
    install_requires=["attrs", "flask", "six"],
    packages=["hondana"],
    package_data={"hondana.templates": "*.html", "hondana.static": "*.css"}
)
