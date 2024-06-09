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

__version__ = "0.0.2"
parser = argparse.ArgumentParser(
    description="Setup Github-Pages on a local machine with Docker."
)
# default values
parser.add_argument("-v", "--version", action="version",
                    version="%(prog)s ver." + __version__)

parser.add_argument("INPUT_DIR", help="Build target directory")

# options : Docker
parser.add_argument("--image_name", type=str, default="github_pages_server_image",
                    help="Docker image name")
parser.add_argument("--image_version", type=str, default="latest",
                    help="Docker image version")
parser.add_argument("--container_name", type=str, default="server_jekyll",
                    help="Docker container name")
# options : Jekyll
parser.add_argument("--port", type=int, default=8000, help="publish port")
parser.add_argument("--output_dir", type=str, default="_site",
                    help="Folder where build results are stored")
# options : Settings
parser.add_argument("--root_dir", type=str,
                    default=os.path.abspath(os.path.join(
                        os.path.dirname(__file__), ".")),
                    help="Root directory")
parser.add_argument("--dockerfile_path", type=str, default="data/Dockerfile",
                    help="Dockerfile path")
parser.add_argument("--node_dir", type=str, default="data/node",
                    help="Server setting directory")
parser.add_argument("--jekyll_dir", type=str, default="data/jekyll",
                    help="jekyll directory")
# options : Control tools
parser.add_argument("--setup", action='store_true',
                    help="Restart the container")
parser.add_argument("--remake_container_only", action='store_true',
                    help="Remake from container")
parser.add_argument("--wait_logs", type=int, default=6,
                    help="Wait before displaying docker logs")


class SetupGithubPages:
    """Setup Github-Pages on a local machine with Docker."""
    _root_dir = "."
    _src = ""
    _output_dir = "_site"
    _dockerfile_path = "data/Dockerfile"
    _node_dir = "data/node"
    _remake_container_only = False
    _setup = False

    def __init__(self, ap):
        """Initialize the class."""
        # =========================================================
        self._root_dir = os.path.abspath(ap.root_dir)
        self._src = os.path.abspath(
            os.path.join(ap.root_dir, ap.INPUT_DIR))
        self._dockerfile_path = os.path.abspath(
            os.path.join(ap.root_dir, ap.dockerfile_path))
        self._output_dir = os.path.abspath(
            os.path.join(ap.root_dir, ap.output_dir))
        self._jekyll_dir = os.path.abspath(
            os.path.join(ap.root_dir, ap.jekyll_dir))
        self._node_dir = os.path.abspath(
            os.path.join(ap.root_dir, ap.node_dir))
        self._remake_container_only = ap.remake_container_only
        self._setup = ap.setup
        if self._remake_container_only is True:
            self._setup = True

        # =========================================================
        ret = self.stop_container(ap.container_name)
        if self._setup is True:
            # If there are any containers using the image, delete them.
            ret = self.remove_container(ap.image_name, ap.image_version)

            # If there is an image with the same name, delete it.
            if self._remake_container_only is False and ret == 0:
                ret = self.remove_image(ap.image_name, ap.image_version)

        if ret == 0:
            # build docker image
            ret = self.build_docker_image(self._root_dir, self._jekyll_dir,
                                          self._dockerfile_path,
                                          ap.image_name, ap.image_version)

        if ret == 0:
            # create docker container
            ret = self.create_docker_container(ap.image_name, ap.image_version,
                                               ap.container_name,
                                               ap.port, self._src,
                                               self._output_dir,
                                               self._node_dir)

        # =========================================================
        if ret == 0:
            self.wait_logs(ap.wait_logs)
            self.print_docker_logs(ap.container_name)
        self.print_container_list()
        # =========================================================

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

    def stop_container(self, container_name: str):
        """Stop Docker container."""
        ret, result = self.get_process(['docker', 'ps', '--format', '"{{.Names}}"',
                                        '--filter', 'name=' + container_name])
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

    def start_container(self, container_name: str):
        """Start Docker container."""
        ret, result = self.get_process(['docker', 'ps', '-a', '--format', '"{{.Names}}"',
                                        '--filter', 'name=' + container_name])
        if ret == 0:
            for item in result.splitlines():
                if item == "":
                    continue
                if item == container_name:
                    ret, _result2 = self.get_process(
                        ['docker', 'start', item])
                    if ret == 0:
                        print("  --> Start container: " + item)
        if ret != 0:
            print("  [ERROR] Failed container Start :" + container_name)
        return ret

    def remove_container(self, image_name: str, image_version: str):
        """Remove Docker container."""
        print("[\n## Remove a container]")
        # ================================
        # If there are any containers using the image, delete them.
        ret, result = self.get_process(['docker', 'ps', '-a', '--format', '"{{.Names}}"',
                                        '--filter', 'ancestor=' + image_name + ':' + image_version])
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

    def remove_image(self, image_name: str, image_version: str):
        """Remove Docker image."""
        print("\n[## Remove a docker image]")
        ret, result = self.get_process(
            ['docker', 'images', '-q', image_name + ':' + image_version])
        if ret == 0:
            if result != "":
                ret, result_rmi = self.get_process(
                    ['docker', 'rmi', image_name + ':' + image_version])
                if ret == 0:
                    print(result_rmi)
                    print(
                        "  --> Remove image: " + image_name + ':' + image_version)
        if ret != 0:
            print("  [ERROR] Don't remove a Docker image")
        return ret

    def build_docker_image(self, root_dir: str, jekyll_dir: str, dockerfile_path: str,
                           image_name: str, image_version):
        """Build Docker Image."""
        print("\n[## Create a Docker image]")
        ret, result = self.get_process(
            ['docker', 'images', '-q', image_name + ':' + image_version])
        if ret == 0:
            if result == "":
                os.chdir(jekyll_dir)
                ret = os.system('docker build'
                                # ' --no-cache'
                                # + ' --build-arg RUBY_VERSION=' + ruby_version
                                + ' -t ' + image_name + ':' + image_version
                                + ' -f' + dockerfile_path
                                + " " + jekyll_dir)
                os.chdir(root_dir)
                if ret == 0:
                    print("  --> Create image: "
                          + image_name + ':' + image_version + "(" + str(ret) + ")")
            else:
                print("  --> Already exists image: "
                      + image_name + ':' + image_version)
        if ret != 0:
            print("  [ERROR] Not get Docker image")
        return ret

    def create_docker_container(self, image_name: str, image_version: str,
                                container_name: str, open_port: int,
                                src: str, output_dir: str, node_dir: str):
        """Create Docker Container."""
        ret, result = self.get_process(['docker', 'ps', '-a', '--format', '"{{.Names}}"',
                                        '--filter', 'name=' + container_name])
        flag_create = True
        if ret == 0:
            for item in result.splitlines():
                if item == "":
                    continue
                if item == container_name:
                    flag_create = False

        print("\n[## Create Docker Container]")
        if flag_create is True:
            ret, _result = self.get_process(
                ['docker', 'run', '-dit',
                 '--name', container_name,
                 '--hostname', container_name,
                 '--publish', str(open_port) + ":8000",
                 '-v', node_dir + ":/root/node",
                 '-v', src + ":/root/src",
                 '-v', output_dir + ":/root/_site",
                 '--workdir', "/root",
                 image_name + ":" + image_version,
                 "/bin/bash"
                 ])
            if ret == 0:
                print("  --> Create Docker container: " + container_name)
                print("        src : " + src)
                print("        dst : " + output_dir)
        else:
            print("  --> Already exists container: " + container_name)
            ret = self.start_container(container_name)
        if ret != 0:
            print("  [ERROR] Not create Docker container")
        return ret

    def print_docker_logs(self, container_name: str):
        """Print Docker Logs."""
        print("\n[## docker logs]")
        ret = os.system('docker logs ' + container_name)
        return ret

    def print_container_list(self):
        """Print Docker Container"""
        print("\n[## Container list] ")
        ret, result = self.get_process(
            ['docker', 'ps', '-a', '--format', '"{{.Names}}\tState[{{.Status}}]\tProt:{{.Ports}}"'])
        if ret == 0 and result != "":
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
