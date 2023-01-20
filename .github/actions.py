import os
import json
import re
import shutil
from pathlib import Path

import jinja2


PACKAGE_INDEX = Path("index.json")
TEMPLATE_DIR = Path('templates')
INDEX_TEMPLATE = Path("index.html")
PKG_TEPLATE = Path("pkg.html")


def normalize(name):
    """From PEP503 : https://www.python.org/dev/peps/pep-0503/"""
    return re.sub(r"[-_.]+", "-", name).lower()


class ActionHandler:
    def __init__(
        self,
        index_file: Path = PACKAGE_INDEX,
        template_dir: Path = TEMPLATE_DIR,
    ):
        self._index_file = index_file
        self._template_dir = template_dir

        self._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(TEMPLATE_DIR)
        )

        self._index = {}
        if self._index_file.exists():
            with open(self._index_file, encoding='utf-8') as f:
                self._index = json.load(f)

    def is_package_registered(self, pkg_name: str):
        return pkg_name in self._index

    def register(self, pkg_name: str, version: str, homepage: str, link: str):
        norm_pkg_name = normalize(pkg_name)
        if self.is_package_registered(norm_pkg_name):
            raise ValueError(f'Package {norm_pkg_name} already registered')

        self._index[norm_pkg_name] = dict(
            name=pkg_name,
            version=version,
            homepage=homepage,
            link=f'{link}#egg={norm_pkg_name}-{version}',
        )

        self.dump_index()
        self.dump_pkg(norm_pkg_name)

    def dump_pkg(self, norm_pkg_name: str):
        pkg_template = self._env.get_template(str(PKG_TEPLATE))
        contents = pkg_template.render(**self._index[norm_pkg_name])

        pkg_path = Path(norm_pkg_name)
        pkg_path.mkdir(exist_ok=True)
        with open(pkg_path / 'index.html', 'w', encoding='utf-8') as html:
            html.write(contents)

    def dump_index(self):
        with open(self._index_file, 'w', encoding='utf-8') as f:
            json.dump(self._index, f, indent=2)

        index_template = self._env.get_template(str(INDEX_TEMPLATE))
        contents = index_template.render(index=self._index.values())

        with open(INDEX_TEMPLATE, 'w', encoding='utf-8') as html:
            html.write(contents)

    def update(self, pkg_name: str, version: str, link: str):
        # FIXME: support storing multiple versions
        norm_pkg_name = normalize(pkg_name)

        if not self.is_package_registered(norm_pkg_name):
            raise ValueError(f'Package {norm_pkg_name} is not registered')

        # FIXME: support omitting args (e.g. link/version) to keep them
        self._index[norm_pkg_name].update(
            version=version, link=f'{link}#egg={norm_pkg_name}-{version}'
        )

        self.dump_index()
        self.dump_pkg(norm_pkg_name)

    def delete(self, pkg_name: str):
        norm_pkg_name = normalize(pkg_name)

        if not self.is_package_registered(norm_pkg_name):
            raise ValueError('Package {norm_pkg_name} is not registered')

        self._index.pop(norm_pkg_name)

        shutil.rmtree(norm_pkg_name)
        self.dump_index()


def main():
    handler = ActionHandler()
    action = os.environ["PKG_ACTION"]

    if action == "REGISTER":
        handler.register(
            pkg_name=os.environ["PKG_NAME"],
            version=os.environ["PKG_VERSION"],
            homepage=os.environ["PKG_HOMEPAGE"],
            link=os.environ["PKG_LINK"],
        )

    elif action == "DELETE":
        handler.delete(pkg_name=os.environ["PKG_NAME"])

    elif action == "UPDATE":
        handler.update(
            pkg_name=os.environ["PKG_NAME"],
            version=os.environ["PKG_VERSION"],
            link=os.environ["PKG_LINK"],
        )


if __name__ == "__main__":
    main()
