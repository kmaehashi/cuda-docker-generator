[![Travis](https://api.travis-ci.org/kmaehashi/cuda-docker-generator.svg?branch=master)](https://travis-ci.org/kmaehashi/cuda-docker-generator)

# cuda-docker-generator

`cuda-docker-generator` is a tool to generate `Dockerfile` that installs CUDA / cuDNN on arbitrary base Docker image.

Installation steps are automatically downloaded from assets in [nvidia/cuda repository](https://gitlab.com/nvidia/cuda/).
Images can be run using [nvidia-docker](https://github.com/NVIDIA/nvidia-docker).

## Usage

The following is an example to generate `Dockerfile` (and `cuda.repo`) that installs development components of CUDA 9.1 for CentOS 7 and cuDNN 7 on Fedora 27 Docker image.

```
$ ./generate.py --os centos7 --cuda 9.1 --cudnn 7 --variant devel --base fedora:27
```

By default, privilege used to run the image is reset to `root`.
You can override this behavior by specifying `--user` option.

```
$ ./generate.py --os ubuntu16.04 --cuda 9.0 --cudnn 7 --base jupyter/datascience-notebook --user jovyan
```

See `./generate.py --help` for the detailed usage.

## Notes

* If you specify `--base` image containing different operating system than one specified in `--os`, CUDA may not work properly.
* If you specify invalid combination (e.g., CUDA 9.1 with cuDNN 6), you may see `HTTP Error 404: Not Found` error.
  `--verbose` option may help diagnosing such issue.
