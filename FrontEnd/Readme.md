## Setup

##### Arch Linux-

the speech-to-text module requires python version >=3.6 and <3.8

Run the following to build python from source and also install shared libraries for `pyinstaller`
Note: Assuming python lib paths are present in `/usr/local/lib`, if not find where it is present in your system and specify it in `LDFLAGS`

```bash
wget https://www.python.org/ftp/python/3.7.12/Python-3.7.12.tgz

tar -xzf Python-3.7.12.tgz
cd Python-3.7.12/
./configure --enable-shared --enable-optimizations LDFLAGS="-Wl,-rpath /usr/local/lib"

make && sudo make install
```

Wait for python to get built and then installed onto your system. This might take 10-20 mins depending on your system

Depending on your system `python3.7` will get installed in a path present in `$PATH` env variable
for ex: `/usr/bin/python3.7`

Ensure pipenv is installed before creating the virtual environment

```bash
pip3 install --user pipenv
```

Now use `python3.7` to create the virtual environment in the same directory as the git clone

```bash
python3.7 -m venv .venv
```

Now activate the virtual environment in the preferred manner and run

```
pipenv install
```

This will install all teh dependencies required.
