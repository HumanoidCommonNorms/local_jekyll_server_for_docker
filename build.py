"""This is a script to set up Github-Pages with Docker on your machine."""
# SYSTEM: Python 3.11.1
#
# これは、Github-PagesをローカルマシンにDockerでセットアップするためのスクリプトです。
#
# このスクリプトは、以下の内容を実行します。
# * .buildフォルダにjekyll-build-pagesをダウンロード
# * jekyll-build-pagesのDockerイメージを作成
# * jekyll-build-pagesのDockerコンテナを作成

import sys
import os
import argparse
import shutil
import subprocess

__version__ = "0.0.1"
parser = argparse.ArgumentParser(
    description="Setup Github-Pages on a local machine with Docker"
)
parser.add_argument("-v", "--version", action="version",
                    version="%(prog)s ver." + __version__)

parser.add_argument("--url", type=str, default="https://github.com/actions/jekyll-build-pages.git",
                    help="URL where jekyll-build-pages can be downloaded")
parser.add_argument("--branch", type=str, default="v1.0.12",
                    help="Branch name of jekyll-build-pages")

parser.add_argument("--image_name", type=str, default="github_pages_build_image",
                    help="Docker image name")
parser.add_argument("--image_version", type=str, default="latest",
                    help="Docker image version")
# https://pages.github.com/versions/
parser.add_argument("--image_option_ruby_version", type=str, default="2.7.4",
                    help="Ruby version")
parser.add_argument("--container_name", type=str, default="build_jekyll",
                    help="Docker container name")
parser.add_argument("--dockerfile_name", type=str, default="Dockerfile",
                    help="Dockerfile name")
parser.add_argument("--gemfile_path", type=str, default="test/.build/Gemfile",
                    help="Gemfile path")

parser.add_argument("--src", type=str, default="docs", help="Build directory")
parser.add_argument("--root_dir", type=str,
                    default=os.path.abspath(os.path.join(
                        os.path.dirname(__file__), "./..")),
                    help="Root directory")
parser.add_argument("--download_dir", type=str, default="test/.build",
                    help="Download directory")
parser.add_argument("--volume_site", type=str, default="_site",
                    help="Folder where build results are stored")
parser.add_argument("--clone_again", action='store_true',
                    help="Execute a git clone again")
parser.add_argument("--remake_image", action='store_true',
                    help="Remake Docker image")


class SetupGithubPages:
    """Setup Github-Pages on a local machine with Docker."""
    _flag_init = False

    _root_dir = "."
    _download_dir = "."
    _src = "docs"
    _volume_site = "_site"
    _gemfile_path = "test/Gemfile"
    _dockerfile_path = "Dockerfile"
    _remake_image = False
    _image_name = "github_pages_build_image"
    _image_version = "latest"
    _url = "https://github.com/actions/jekyll-build-pages.git"
    _branch = "v1.0.12"
    _image_option_ruby_version = "2.7.4"
    _container_name = "build_jekyll"
    _clone_again = False

    def _set_args(self, ap):
        self._root_dir = os.path.abspath(ap.root_dir)
        self._download_dir = os.path.abspath(
            os.path.join(ap.root_dir, ap.download_dir))
        self._src = os.path.abspath(
            os.path.join(ap.root_dir, ap.src))
        self._volume_site = os.path.abspath(
            os.path.join(ap.root_dir, ap.volume_site))
        self._gemfile_path = os.path.abspath(
            os.path.join(ap.root_dir, ap.gemfile_path))
        self._dockerfile_path = os.path.abspath(
            os.path.join(self._download_dir, ap.dockerfile_name))
        self._remake_image = ap.remake_image
        if ap.clone_again is True:
            self._remake_image = True
        self._image_name = ap.image_name
        self._image_version = ap.image_version
        self._url = ap.url
        self._branch = ap.branch
        self._clone_again = ap.clone_again
        self._image_option_ruby_version = ap.image_option_ruby_version
        self._container_name = ap.container_name

        self._flag_init = True

    def __init__(self, ap):
        """Initialize the class."""
        # =========================================================
        self._set_args(ap)
        # =========================================================

        # =========================================================
        # If there are any containers using the image, delete them.
        ret = self.remove_container()

        # =========================================================
        # If there is an image with the same name, delete it.
        if self._remake_image is True:
            if ret == 0:
                ret = self.remove_image()

        # =========================================================
        if ret == 0:
            ret = self.download_jekyll_build_pages()

        # =========================================================
        if ret == 0:
            ret = self.build_docker_image()

        # =========================================================
        if ret == 0:
            ret = self.create_docker_container()

        # =========================================================
        # self.print_container_list()
        # self.print_docker_logs(ap.container_name)
        # =========================================================

    def download_jekyll_build_pages(self):
        """Download jekyll-build-pages."""
        print("[## Download jekyll-build-pages]")
        ret = 1
        if self._flag_init is True:
            ret = 0
            _flag_download = True
            # Delete the existing directory
            if os.path.exists(self._download_dir):
                if self._clone_again is True:
                    print("  --> Remove directory: " + self._download_dir)
                    shutil.rmtree(self._download_dir)
                    _flag_download = True
                else:
                    print("  --> exists directory: " + self._download_dir)
                    _flag_download = False

            if _flag_download is True:
                # Clone the repository
                ret, result = self.get_process(['git', 'clone', '--quiet',
                                                '--no-progress', self._url,
                                                '--branch', self._branch, self._download_dir])
                if ret == 0:
                    print("  --> Get clone " + self._url
                          + "(" + self._branch + ")")
                else:
                    print("  [ERROR] " + result)
        return ret

    def start_container(self):
        """Start Docker container."""
        ret, result = self.get_process(['docker', 'ps', '-a', '--format', '"{{.Names}}"',
                                        '--filter', 'name=' + self._container_name])
        if ret == 0:
            for item in result.splitlines():
                if item == "":
                    continue
                if item == self._container_name:
                    ret, _result2 = self.get_process(['docker', 'start', item])
                    if ret == 0:
                        print("  --> Start container: " + item)
        if ret != 0:
            print("  [ERROR] Failed container Start :" + self._container_name)
        return ret

    def remove_container(self):
        """Remove Docker container."""
        ret = 1
        if self._flag_init is True:
            print("[## Remove a container]")
            # ================================
            # If there are any containers using the image, delete them.
            ret, result = self.get_process(['docker', 'ps', '-a', '--format', '"{{.Names}}"',
                                            '--filter', 'ancestor='
                                            + self._image_name + ':' + self._image_version])
            if ret == 0:
                for container_name in result.splitlines():
                    if container_name == "":
                        continue
                    ret, _result2 = self.get_process(
                        ['docker', 'rm', '-f', container_name])
                    print("  --> Remove container: "
                          + container_name + "(" + str(ret) + ")")
        return ret

    def remove_image(self):
        """Remove Docker image."""
        ret = 1
        if self._flag_init is True:
            print("[## Remove a docker image]")
            ret, result = self.get_process(
                ['docker', 'images', '-q', self._image_name + ':' + self._image_version])
            if result != "":
                ret, _result2 = self.get_process(
                    ['docker', 'rmi', self._image_name + ':' + self._image_version])
                if ret == 0:
                    print(
                        "  --> Remove image: " + self._image_name + ':' + self._image_version)
            if ret != 0:
                print("  [ERROR] Don't remove a Docker image")
        return ret

    def build_docker_image(self):
        """Build Docker Image."""
        ret = 1
        if self._flag_init is True:
            print("[## Create a Docker image]")
            ret, result = self.get_process(
                ['docker', 'images', '-q', self._image_name + ':' + self._image_version])
            if ret == 0 and result == "":
                os.chdir(self._download_dir)
                ret = os.system('docker build'
                                # + ' --no-cache'
                                + ' --build-arg RUBY_VERSION=' + self._image_option_ruby_version
                                + ' -t ' + self._image_name + ':' + self._image_version
                                + ' -f' + self._dockerfile_path
                                + " " + self._download_dir)
                os.chdir(self._root_dir)
                if ret == 0:
                    print("  --> Create image: "
                          + self._image_name + ':' + self._image_version)
                else:
                    print("  [ERROR] Don't create a Docker image")
            else:
                print("  --> Already exists image: "
                      + self._image_name + ':' + self._image_version)
            if ret != 0:
                print("  [ERROR] Not get Docker image")

        return ret

    def create_docker_container(self):
        """Create Docker Container."""
        ret = 1
        if self._flag_init is True:
            ret, result = self.get_process(['docker', 'ps', '-a', '--format', '"{{.Names}}"',
                                            '--filter', 'name=' + self._container_name])
            flag_create = True
            if ret == 0:
                for item in result.splitlines():
                    if item == "":
                        continue
                    if item == self._container_name:
                        flag_create = False

            if flag_create is True:
                print("[## Create Docker Container]")
                ret, _result = self.get_process(
                    ['docker', 'run', '-dit',
                     '--name', self._container_name,
                     '--hostname', self._container_name,
                     '--rm',
                     '-v', self._gemfile_path + ":/root/src/Gemfile",
                     '-v', self._src + ":/root/src",
                     '-v', self._volume_site + ":/root/_site",
                     '-e', "GITHUB_WORKSPACE=/root",
                     '-e', "INPUT_SOURCE=src",
                     '-e', "INPUT_DESTINATION=_site",
                     '-e', "INPUT_FUTURE=true",
                     '-e', "INPUT_VERBOSE=true",
                     '-e', "INPUT_TOKEN=",
                     '-e', "INPUT_BUILD_REVISION=",
                     '--workdir', "/",
                     self._image_name + ":" + self._image_version,
                     "/bin/bash"
                     ])
                if ret == 0:
                    print("  --> Create Docker container: "
                          + self._container_name)
                    print("        src:         " + self._src)
                    print("        volume_site: " + self._volume_site)
            else:
                print("  --> Already exists container: " + self._container_name)
                ret = self.start_container()
            if ret != 0:
                print("  [ERROR] Not create Docker container")
        return ret

    def print_docker_logs(self, container_name: str):
        """Print Docker Logs."""
        print("[## docker logs]")
        ret = os.system('docker logs ' + container_name)
        return ret

    def print_container_list(self):
        """Print Docker Container"""
        print("[## Container list] ")
        ret, result = self.get_process(
            ['docker', 'ps', '-a', '--format', '"{{.Names}} : {{.Status}}"'])
        if ret == 0:
            print("--------------------------------------------------")
            print(result)
            print("--------------------------------------------------")
        return ret

    def process_run(self, cmd: str, work_dir: str = ""):
        """Run the process."""
        try:
            if work_dir == "":
                work_dir = self._root_dir
            proc = subprocess.run(
                cmd, check=True, shell=True, cwd=work_dir, stdout=subprocess.PIPE)
            stdout = proc.stdout
            str_type = type(stdout)
            if str_type is bytes:
                stdout = stdout.decode('utf-8').replace('"', '')
            else:
                stdout = str(stdout).replace('"', '')
            return proc.returncode, stdout
        except ImportError as e:
            return 1, str(e)

    def get_process(self, cmd: str, work_dir: str = ""):
        """Get the process."""
        try:
            if work_dir == "":
                work_dir = self._root_dir
            proc = subprocess.run(
                cmd, check=True, shell=True, cwd=work_dir, stdout=subprocess.PIPE)
            stdout = proc.stdout
            str_type = type(stdout)
            if str_type is bytes:
                stdout = stdout.decode('utf-8').replace('"', '')
            else:
                stdout = str(stdout).replace('"', '')
            return proc.returncode, stdout
        except ImportError as e:
            return 1, str(e)


if __name__ == "__main__":
    args = parser.parse_args()
    try:
        setup = SetupGithubPages(args)
    except ImportError as imp_error:
        print("[ERROR] " + str(imp_error))

    sys.exit(0)
