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
import time

__version__ = "0.0.2"
parser = argparse.ArgumentParser(
    description="Setup Github-Pages on a local machine with Docker"
)
parser.add_argument("-v", "--version", action="version",
                    version="%(prog)s ver." + __version__)
parser.add_argument("INPUT_DIR", help="Build target directory")

# Settings: jekyll-build-pages
parser.add_argument("--url", type=str, default="https://github.com/actions/jekyll-build-pages.git",
                    help="URL where jekyll-build-pages can be downloaded")
parser.add_argument("--branch", type=str, default="v1.0.12",
                    help="Branch name of jekyll-build-pages")
parser.add_argument("--download_dir", type=str, default=".build",
                    help="Download directory")

# Settings: Docker
# ## Please check ruby version: https://pages.github.com/versions/
parser.add_argument("--image_name", type=str, default="github_pages_build_image",
                    help="Docker image name")
parser.add_argument("--image_version", type=str, default="latest",
                    help="Docker image version")
parser.add_argument("--image_option_ruby_version", type=str, default="3.1.6",
                    help="Ruby version")
parser.add_argument("--container_name", type=str, default="build_jekyll",
                    help="Docker container name")
parser.add_argument("--dockerfile_name", type=str, default="Dockerfile",
                    help="Dockerfile name")
parser.add_argument("--entrypoint_name", type=str, default="entrypoint.sh",
                    help="entrypoint name")

# Settings: default
parser.add_argument("--root_dir", type=str,
                    default=os.path.abspath(os.path.dirname(__file__)),
                    help="Root directory")

# Settings: jekyll
parser.add_argument("--gemfile_path", type=str, default=".build/Gemfile",
                    help="Gemfile path")
parser.add_argument("--volume_site", type=str, default="_site",
                    help="Folder where build results are stored")

# Options : Control tools
parser.add_argument("--clone_again", action='store_true',
                    help="Execute a git clone again")
parser.add_argument("--remake_image", action='store_true',
                    help="Remake Docker image")
parser.add_argument("--wait_logs", type=int, default=6,
                    help="Wait before displaying docker logs")


class SetupGithubPages:
    """Setup Github-Pages on a local machine with Docker."""
    _flag_init = False

    _root_dir = "."
    _download_dir = "."
    _src = "."
    _volume_site = "_site"
    _gemfile_path = ".build/Gemfile"
    _dockerfile_path = "Dockerfile"
    _entrypoint_name = "entrypoint.sh"
    _remake_image = False
    _image_name = "github_pages_build_image"
    _image_version = "latest"
    _url = "https://github.com/actions/jekyll-build-pages.git"
    _branch = "v1.0.12"
    _image_option_ruby_version = "2.7.4"
    _container_name = "build_jekyll"
    _wait_logs = 6
    _clone_again = False

    def _set_args(self, ap):
        self._root_dir = os.path.abspath(ap.root_dir)
        self._download_dir = os.path.abspath(
            os.path.join(ap.root_dir, ap.download_dir))
        self._src = os.path.abspath(
            os.path.join(ap.root_dir, ap.INPUT_DIR))
        self._volume_site = os.path.abspath(
            os.path.join(ap.root_dir, ap.volume_site))
        self._gemfile_path = os.path.abspath(
            os.path.join(ap.root_dir, ap.gemfile_path))
        self._dockerfile_path = os.path.abspath(
            os.path.join(self._download_dir, ap.dockerfile_name))
        self._entrypoint_name = os.path.abspath(
            os.path.join(self._download_dir, ap.entrypoint_name))
        self._remake_image = ap.remake_image
        self._image_name = ap.image_name
        self._image_version = ap.image_version
        self._url = ap.url
        self._branch = ap.branch
        self._clone_again = ap.clone_again
        self._image_option_ruby_version = ap.image_option_ruby_version
        self._container_name = ap.container_name
        self._wait_logs = ap.wait_logs

        if self._clone_again is True:
            self._remake_image = True

        self._flag_init = True

    def __init__(self, ap):
        """Initialize the class."""
        # =========================================================
        self._set_args(ap)

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
        if ret == 0:
            self.wait_logs()
            self.print_docker_logs()
        # =========================================================
        # if ret == 0:
        #     self.stop_container()
        # =========================================================

    def download_jekyll_build_pages(self):
        """Download jekyll-build-pages."""
        print("\n[## Download jekyll-build-pages]")
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
                # check and change autocrlf
                flag_autocrlf = "false"
                ret, result = self.get_process(
                    ['git', 'config', '--global', 'core.autocrlf'])
                if ret == 0 and result != "":
                    flag_autocrlf = result.rstrip('\n')
                print("  --> git config core.autocrlf " + flag_autocrlf)
                ret, result = self.get_process(
                    ['git', 'config', '--global', 'core.autocrlf', "input"])
                if ret == 0:
                    print("  --> git config core.autocrlf input")

                    # Clone the repository
                    ret, result = self.get_process(['git', 'clone', '--quiet',
                                                    '--no-progress', self._url,
                                                    '--branch', self._branch, self._download_dir])
                    if ret == 0:
                        print("  --> Get clone " + self._url
                              + "(" + self._branch + ")")
                    else:
                        print("  [ERROR] " + result)
                _ret, _result = self.get_process(
                    ['git', 'config', '--global', 'core.autocrlf', flag_autocrlf])
                _ret, result = self.get_process(
                    ['git', 'config', '--global', 'core.autocrlf'])
                if _ret == 0 and result != "":
                    print("  --> git config core.autocrlf " + result.rstrip('\n'))

        return ret

    def stop_container(self):
        """Stop Docker container."""
        ret = 1
        if self._flag_init is True:
            ret, result = self.get_process(['docker', 'ps', '--format', '"{{.Names}}"',
                                            '--filter', 'name=' + self._container_name])
            if ret == 0:
                for item in result.splitlines():
                    if item == "":
                        continue
                    ret, _result2 = self.get_process(
                        ['docker', 'stop', item])
                    if ret == 0:
                        print("  --> Stop container: " + item)
        if ret != 0:
            print("  [ERROR] Failed container stop")
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
            print("\n[## Remove a container]")
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
            print("\n[## Remove a docker image]")
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
            print("\n[## Create a Docker image]")
            print("  dir: " + self._download_dir)
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
                print("\n[## Create Docker Container]")
                ret, _result = self.get_process(
                    ['docker', 'run', '-dit',
                     '--name', self._container_name,
                     '--hostname', self._container_name,
                     # '--rm',
                     '-v', self._gemfile_path + ":/root/src/Gemfile",
                     # '-v', self._entrypoint_name + ":/entrypoint.sh",
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
                    print("        src : " + self._src)
                    print("        site: " + self._volume_site)
            else:
                print("  --> Already exists container: " + self._container_name)
                ret = self.start_container()
            if ret != 0:
                print("  [ERROR] Not create Docker container")
        return ret

    def print_docker_logs(self):
        """Print Docker Logs."""
        print("\n[## docker logs]")
        ret = os.system('docker logs ' + self._container_name)
        return ret

    def print_container_list(self):
        """Print Docker Container"""
        print("\n[## Container list] ")
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

    def wait_logs(self):
        """Wait for a while."""
        print("\n[## Wait: " + str(self._wait_logs) + " sec]")
        _next_line_max = 30
        for _i in range(self._wait_logs):
            time.sleep(1)
            if _i % _next_line_max == (_next_line_max - 1):
                print(".")
            else:
                print("", end='.')
        print("")


if __name__ == "__main__":
    args = parser.parse_args()
    try:
        setup = SetupGithubPages(args)
    except ImportError as imp_error:
        print("[ERROR] " + str(imp_error))

    sys.exit(0)
