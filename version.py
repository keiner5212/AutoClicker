import toml;
filename='pyproject.toml';
project='project';
version='version';
print(toml.load(filename)[project][version])