# Getting started

Thanks for giving us a chance :partying_face:. To get started, you need a minimum knowledge of the terminal to install and launch the application. Don't worry, it's actually very simple. If you think you need to review some concepts, we recommend that you read this [first steps guide](https://realpython.com/terminal-commands/){target=_blank} from Real Python.

## Requirements
Pub Analyzer requires **Python 3.10 or later** (If you can choose, we always recommend the [newest version of Python](https://www.python.org/downloads/){target=_blank} available). If you use a linux distribution with a system-dependent version of Python like Ubuntu that currently uses Python 3.8, you can use [pyenv](https://github.com/pyenv/pyenv){target=_blank}.

!!! warning "For Windows users: `The term 'pip' is not recognized as the name of a cmdlet, function...`"
    A large number of users have written to us that they cannot install pub-analyzer due to this error. The error occurs because the **Add Python to PATH** option was not selected during the Python installation process.

    :wrench: **Quick Fix:** Reinstall Python and during installation, make sure to check the box labelled as **Add Python to PATH**. [More Info](https://docs.python.org/3/using/windows.html#:~:text=On%20the%20first%20page%20of,pip%20for%20the%20package%20installer.){target=_blank}.


Pub Analyzer is a **cross-platform** app, this means it runs on Linux, macOS, and Windows. But the rendering of colors within the application depends on the **terminal** you use. If this is not a problem for you, any terminal will do the job, otherwise, more details below.

### Linux
All Linux distributions come with a terminal emulator that can run Pub Analyzer properly. Nothing to worry about here.

### MacOS
The default Terminal app is limited to 256 colors, resulting in inaccurate color representation (Trust me, the app doesn't look good at all :melting_face:). So we recommend that you use [iTerm2](https://iterm2.com/){target=_blank}.

### Windows
There's really not much to say. You should definitely go straight for the new [Windows Terminal](https://apps.microsoft.com/store/detail/9N0DX20HK701){target=_blank}, you will have a better experience.

## Installation

Install Pub Analyzer via PyPI, with the following command in the terminal:

```
pip install pub-analyzer
```

We aim to maintain a minimal list of dependencies, but keep in mind that the project is in a very early stage, and significant changes might occur. You may prefer to keep the installation in an isolated environment using [venv](https://docs.python.org/3/library/venv.html){target=_blank}.

If a new version is released, you can update using pip with the following command:

```
pip install -U pub-analyzer
```

## Run it

Everything is ready to go :rocket:. Open the app with the following command:

```
pub-analyzer
```

You should see the following:

```{.textual path="pub_analyzer/main.py" columns=90}
```

## Need help?

The [User Guide](./user/index.md) section is the best place to understand how to use Pub Analyzer. If you have more questions, go to the [Help](./help.md) section.
