# codepet

codepet is a small terminal tamagotchi. The pet is a penguin that eats your git
commits: every new commit feeds it, and when you stop coding it slowly gets
hungry.

It uses only the Python standard library at runtime. `pytest` is needed only for
development, and `git` must be installed.

## Requirements

- Linux with Python 3.10 or newer
- `git` on your `PATH`

## Run it

Run these commands from the repository root, the folder that contains `main.py`:

```bash
python main.py
```

The first run creates a pet named Bit in `~/.local/share/codepet/state.json`
(or under `$XDG_DATA_HOME` when that variable is set). Add a repository to watch:

```bash
python main.py add-repo ~/code/my-project
```

After your next commit, run `python main.py` again and the pet eats it.

## Commands

| Command | What it does |
| --- | --- |
| `python main.py` | Update hunger, eat new commits and show the pet |
| `python main.py add-repo PATH` | Watch a git repository (only later commits count) |
| `python main.py remove-repo PATH` | Stop watching a repository |
| `python main.py repos` | List watched repositories |
| `python main.py rename NAME` | Rename the pet |

Hunger drops by one point per hour. Each commit gives +15 hunger and +10 xp,
up to 10 commits per day. The pet grows from egg to baby, teen and adult as it
gains xp. At zero hunger it becomes a ghost, but it comes back as soon as it is
fed.

## Run the tests

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The virtual environment keeps `pytest` away from the system Python, which is
useful on Fedora where the system interpreter may refuse user installs.

## Greet me in every terminal

Add this line to your `~/.bashrc`, using the real path to this project:

```bash
python ~/path/to/codepet/main.py
```

Every new terminal then shows the pet and feeds it any commits made since the
last check.

## Project layout

The repository root looks like this:

```text
codepet/
├── main.py
├── codepet/
│   ├── __init__.py
│   ├── pet.py
│   ├── art.py
│   ├── gitlog.py
│   ├── storage.py
│   └── cli.py
├── tests/
│   ├── test_pet.py
│   ├── test_storage.py
│   └── test_gitlog.py
├── requirements-dev.txt
├── .gitignore
└── README.md
```
