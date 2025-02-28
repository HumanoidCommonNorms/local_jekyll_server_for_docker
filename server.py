"""This is a script to set up Github-Pages with Docker on your machine."""
# SYSTEM: Python 3.11.1
#
# これは、Jekyllサーバを立てるスクリプトです。
#
# このスクリプトは、以下の内容を実行します。
# * jekyll-build-pagesのDockerイメージを作成
# * jekyll-build-pagesのDockerコンテナを作成
#   * デーモンで起動する、ビルド失敗したら起動しません

import sys
import os
import argparse
import subprocess
import time


class JekyllServerOptions:
    """Default options."""
    flag_init = False

    root_dir = os.path.dirname(__file__)
    src = "."
    image_name = "github_pages_server_image"
    image_version = "latest"
    container_name = "server_jekyll"
    port = 8010
    output_dir = "_site"
    dockerfile_path = "data/Dockerfile"
    node_dir = "data/node"
    jekyll_dir = "data/jekyll"
    setup = False
    remake_container = False
    wait_logs = 6

    def set_args(self, ap):
        """Set the arguments."""
        self.root_dir = os.path.abspath(ap.root_dir)
        self.src = os.path.abspath(
            os.path.join(ap.root_dir, ap.INPUT_DIR))
        self.image_name = ap.image_name
        self.image_version = ap.image_version
        self.container_name = ap.container_name
        self.port = ap.port
        self.output_dir = os.path.abspath(
            os.path.join(ap.root_dir, ap.output_dir))
        self.dockerfile_path = os.path.abspath(
            os.path.join(ap.root_dir, ap.dockerfile_path))
        self.node_dir = os.path.abspath(
            os.path.join(ap.root_dir, ap.node_dir))
        self.jekyll_dir = os.path.abspath(
            os.path.join(ap.root_dir, ap.jekyll_dir))
        self.setup = ap.setup
        self.remake_container = ap.remake_container
        if self.remake_container is True:
            self.setup = True
        self.wait_logs = ap.wait_logs

        self.flag_init = True

    def __init__(self):
        pass


__version__ = "0.0.3"
options = JekyllServerOptions()
parser = argparse.ArgumentParser(
    description="Setup Github-Pages on a local machine with Docker."
)
parser.add_argument("-v", "--version", action="version",
                    version="%(prog)s ver." + __version__)
parser.add_argument("INPUT_DIR", help="Build target directory")

# options : Docker
parser.add_argument("--image_name", type=str, default=options.image_name,
                    help="Docker image name / Default=" + options.image_name)
parser.add_argument("--image_version", type=str, default=options.image_version,
                    help="Docker image version / Default=" + options.image_version)
parser.add_argument("--container_name", type=str, default=options.container_name,
                    help="Docker container name / Default=" + options.container_name)
parser.add_argument("--dockerfile_path", type=str, default=options.dockerfile_path,
                    help="Dockerfile relative path / Default=" + options.dockerfile_path)
# options : Jekyll
parser.add_argument("--port", type=int,
                    default=options.port, help="publish port / Default=" + str(options.port))
parser.add_argument("--output_dir", type=str, default="_site",
                    help="Folder where build results are stored")
# options : Settings
parser.add_argument("--root_dir", type=str, default=options.root_dir,
                    help="Root directory / Default=" + options.root_dir)
parser.add_argument("--node_dir", type=str, default=options.node_dir,
                    help="Server setting directory / Default=" + options.node_dir)
parser.add_argument("--jekyll_dir", type=str, default=options.jekyll_dir,
                    help="jekyll directory / Default=" + options.jekyll_dir)
# options : Control tools
parser.add_argument("--setup", action='store_true', help="Restart the container")
parser.add_argument("--remake_container", action='store_true', help="Remake from container")
parser.add_argument("--wait_logs", type=int, default=options.wait_logs,
                    help="Wait before displaying docker logs / Default=" + str(options.wait_logs))


class SetupGithubPages:
    """Setup Github-Pages on a local machine with Docker."""
    _opt = JekyllServerOptions()

    def __init__(self, opt: JekyllServerOptions):
        """Initialize the class."""
        # =========================================================
        self._opt = opt

        # =========================================================
        ret = self.stop_container()
        if self._opt.setup is True:
            # If there are any containers using the image, delete them.
            ret = self.remove_container()

            # If there is an image with the same name, delete it.
            if self._opt.remake_container is False and ret == 0:
                ret = self.remove_image()

        if ret == 0:
            # build docker image
            ret = self.build_docker_image()

        if ret == 0:
            # create docker container
            ret = self.create_docker_container()

        # =========================================================
        if ret == 0:
            self.wait_logs(self._opt.wait_logs)
            self.print_docker_logs()
        self.print_container_list()
        # =========================================================

    def stop_container(self):
        """Stop Docker container."""
        ret = 1
        if self._opt.flag_init is True:
            ret, result = self.get_process(['docker', 'ps', '--format', '"{{.Names}}"',
                                            '--filter', 'name=' + self._opt.container_name])
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
        ret = 1
        if self._opt.flag_init is True:
            ret, result = self.get_process(['docker', 'ps', '-a', '--format', '"{{.Names}}"',
                                            '--filter', 'name=' + self._opt.container_name])
            if ret == 0:
                for item in result.splitlines():
                    if item == "":
                        continue
                    if item == self._opt.container_name:
                        ret, _result2 = self.get_process(
                            ['docker', 'start', item])
                        if ret == 0:
                            print("  --> Start container: " + item)
        if ret != 0:
            print("  [ERROR] Failed container Start :"
                  + self._opt.container_name)
        return ret

    def remove_container(self):
        """Remove Docker container."""
        ret = 1
        if self._opt.flag_init is True:
            print("[\n## Remove a container]")
            # ================================
            # If there are any containers using the image, delete them.
            ret, result = self.get_process(['docker', 'ps', '-a', '--format', '"{{.Names}}"',
                                            '--filter', 'ancestor='
                                            + self._opt.image_name + ':' + self._opt.image_version])
            if ret == 0:
                for container_name in result.splitlines():
                    if container_name == "":
                        continue
                    ret2, _result2 = self.get_process(
                        ['docker', 'rm', '-f', container_name])
                    print(
                        "  --> Remove container: " + container_name + "(" + str(ret2) + ")")
            else:
                print("  [ERROR] Don't call docker ps")
        return ret

    def remove_image(self):
        """Remove Docker image."""
        ret = 1
        if self._opt.flag_init is True:
            print("\n[## Remove a docker image]")
            ret, result = self.get_process(
                ['docker', 'images', '-q', self._opt.image_name + ':' + self._opt.image_version])
            if ret == 0:
                if result != "":
                    ret, result_rmi = self.get_process(
                        ['docker', 'rmi', self._opt.image_name + ':' + self._opt.image_version])
                    if ret == 0:
                        print(result_rmi)
                        print("  --> Remove image: "
                              + self._opt.image_name + ':' + self._opt.image_version)
            if ret != 0:
                print("  [ERROR] Don't remove a Docker image")
        return ret

    def build_docker_image(self):
        """Build Docker Image."""
        ret = 1
        if self._opt.flag_init is True:
            print("\n[## Create a Docker image]")
            ret, result = self.get_process(
                ['docker', 'images', '-q', self._opt.image_name + ':' + self._opt.image_version])
            if ret == 0:
                if result == "":
                    os.chdir(self._opt.jekyll_dir)
                    ret = os.system('docker build'
                                    # ' --no-cache'
                                    # + ' --build-arg RUBY_VERSION=' + ruby_version
                                    + ' -t ' + self._opt.image_name + ':' + self._opt.image_version
                                    + ' -f' + self._opt.dockerfile_path
                                    + " " + self._opt.jekyll_dir)
                    os.chdir(self._opt.root_dir)
                    if ret == 0:
                        print("  --> Create image: "
                              + self._opt.image_name + ':' + self._opt.image_version
                              + "(" + str(ret) + ")")
                else:
                    print("  --> Already exists image: "
                          + self._opt.image_name + ':' + self._opt.image_version)
            if ret != 0:
                print("  [ERROR] Not get Docker image")
        return ret

    def create_docker_container(self):
        """Create Docker Container."""
        ret = 1
        if self._opt.flag_init is True:
            ret, result = self.get_process(['docker', 'ps', '-a', '--format', '"{{.Names}}"',
                                            '--filter', 'name=' + self._opt.container_name])
            flag_create = True
            if ret == 0:
                for item in result.splitlines():
                    if item == "":
                        continue
                    if item == self._opt.container_name:
                        flag_create = False

            print("\n[## Create Docker Container]")
            if flag_create is True:
                ret, _result = self.get_process(
                    ['docker', 'run', '-dit',
                     '--name', self._opt.container_name,
                     '--hostname', self._opt.container_name,
                     '--publish', str(self._opt.port) + ":8000",
                     '-v', self._opt.node_dir + ":/root/node",
                     '-v', self._opt.src + ":/root/src",
                     '-v', self._opt.output_dir + ":/root/_site",
                     '--workdir', "/root",
                     self._opt.image_name + ":" + self._opt.image_version,
                     "/bin/bash"
                     ])
                if ret == 0:
                    print("  src : " + self._opt.src)
                    print("  site: " + self._opt.output_dir)
                    print("  --> Create Docker container: "
                          + self._opt.container_name)
            else:
                print("  --> Already exists container: "
                      + self._opt.container_name)
                ret = self.start_container()
            if ret != 0:
                print("  [ERROR] Not create Docker container")
        return ret

    def wait_logs(self, wait_time_sec: int):
        """Wait for a while."""
        print("\n[## Wait: " + str(wait_time_sec) + " sec]")
        _next_line_max = 30
        for _i in range(wait_time_sec):
            time.sleep(1)
            if _i % _next_line_max == (_next_line_max - 1):
                print(".")
            else:
                print("", end='.')
        print("")

    def print_docker_logs(self):
        """Print Docker Logs."""
        ret = 1
        if self._opt.flag_init is True:
            print("\n[## docker logs]")
            ret = os.system('docker logs ' + self._opt.container_name)
        return ret

    def print_container_list(self):
        """Print Docker Container"""
        ret = 1
        if self._opt.flag_init is True:
            print("\n[## Container list] ")
            ret, result = self.get_process(
                ['docker', 'ps', '-a',
                 '--format', '"{{.Names}}\tState[{{.Status}}]\tProt:{{.Ports}}"'])
            if ret == 0 and result != "":
                print("--------------------------------------------------")
                print(result)
                print("--------------------------------------------------")
        return ret

    def process_run(self, cmd: str, work_dir: str = ""):
        """Run the process."""
        try:
            if work_dir == "":
                work_dir = self._opt.root_dir
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
                work_dir = self._opt.root_dir
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
        options.set_args(args)
        setup = SetupGithubPages(options)
    except ImportError as imp_error:
        print("[ERROR] " + str(imp_error))

    sys.exit(0)
