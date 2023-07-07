# server-user

The chair of e-Finance held by Prof. Gomber provides associated researchers and students with the compute resources and data necessary for data-driven research at scale. 

This user repository includes both documentation and utility software for the e-Finance server landscape.



## On-boarding

All servers run [JupyterHub](https://jupyterhub.readthedocs.io/en/latest/) in order to let users access compute resources through [Jupyter Notebook](https://jupyter-notebook.readthedocs.io/en/latest/) and [Jupyter Lab](https://jupyterlab.readthedocs.io/en/latest/) user interface. To familiarize yourself with the user interface, it may be sensible for you to read up on the documentation. 

Below, we will describe the on-boarding process in detail.

1. When you have been provided with your user name and the server address, please make your first **login** as soon as possible given that you yourself will need to set your password. Neither will you be provided with an initial password, nor will you be able to change an already set password later on - whatever string you type in during your first login will remain your password. 

2. Having logged in, you will be able to start a jupyter **server** (user instance) - depending on your user name, the JupyterHub will give you different configuration options to choose from. Note that user names with `stud_` prefix will *not* have access to GPU-enabled image option(s) `[deep_learning]` as well as larger resource options(s) `[large, extra_large]`. Those students that *do* require access to those resources will be assigned a user name *without* `stud_` prefix. 

3. Having started a jupyter server, you will be able to use multiple Python (R, Julia, ...) **kernels** to run multiple programs at the same time, please understand that you do *not* need multiple jupyter servers! While we allow that you set up a second jupyter server (named server), please also understand that this will not help you lift resource limits as those are defined on a per-user basis. Use named servers *only* as a means to organize your code base. 

4. It is then time to have a look into the [user-manual](user-manual) that will hopefully answer all of your questions. Since you are working on a high-performance computing machine that allows for massive parallelization, we provide you with [examples](user-manual/examples) that will help you write better and more efficient code. In comparison to your private machine, please understand that your program will not run much faster on this machine if your code is not optimized for parallelization!

5. In some cases, we require that you utilize the [user-lib](user-lib), e.g. when it comes to GPU-enabled jobs. In other cases, it will provide you with useful functionality that makes life on the JupyterHub much easier. 

6. Lastly, we encourage you to subscribe to our **message feed** that connects admins (inform about downtime, require user action) and users (ask questions, report issues), allowing for a better overall experience through a speed-up in communication. See [user-feed](user-feed) for more details on the message feed. Should you run into any issues, please do not hesitate to contact us via message feed (preferred) or via e-mail (contact information below).

7. Have fun!



## Guidelines

Please use resources such as CPU, GPU, and memory responsibly so that all users get the best possible performance. The following guidelines can help you avoid unnecessary resource consumption.

1. With regard to the available resource options, select the environment for your jupyter server to be as small as possible (as large as necessary). 

2. Work in your home folder (user storage) where only admins will be able to see your data. Use the mounted directory `/_shared_storage/temp_stud` *only* if you want to share data with other users, and please understand that *every* user has read and write permissions for this folder, which is why your data may not be safe!

3. To identify yourself, please create a txt-file in your home directory called `_yourfirstname_yourlastname.txt`. This enables us to easily identify you as a user.

4. Terminate kernels that you do not require anymore. Although we use a kernel culling mechanism to release bound resources after a pre-defined period of kernel inactivity, you will help us optimize resource usage if you take action yourself. 

5. Shut down your server after finishing your work. Although we use a server culling mechanism to shut down the kubernetes pods running your server after a pre-defined period of user inactivity, you will help us optimize resource usage if you take action yourself. 

6. When using a GPU, we need you to *always* use the `lib.gpu.GpuManager` provided as part of the [user-lib](user-lib). This is to make sure that you do not crash GPU-enabled jobs of other users (they will not be happy ...). Although you theoretically could - do *not* work around this solution! 



## Environments

Listed below are the current image and resource options available for each server. 

**Aime.** SOTA compute server with GPU support that is used primarily for research (data science, deep learning, ...), but also for teaching (theses, seminars, ...). 

Image options: 
```json
{
    "plain_vanilla": {
        "display_name": "Plain Vanilla Environment",
        "description": "For simple jobs that do not require additional frameworks. Based on jupyter/base-notebook:6e246ea4bbff docker image.",
        "kubespawner_override": {
            "image": "jupyter/base-notebook:6e246ea4bbff",
        },
    },
    "data_science": {
        "display_name": "Data Science Environment",
        "description": "For CPU-based data science jobs. Based on jupyter/datascience-notebook:92ce0af9989f docker image.",
        "kubespawner_override": {
            "image": "jupyter/datascience-notebook:92ce0af9989f",
        },
    },
    "deep_learning": {
        "display_name": "Deep Learning Environment",
        "description": "For GPU-accelerated deep learning jobs (A100). Based on cschranz/gpu-jupyter:latest docker image.",
        "kubespawner_override": {
            "image": "cschranz/gpu-jupyter:latest",
        },
    },
}
```

Resource options:
```json
{
    "small": {
        "cpu_limit": 1,
        "cpu_guarantee": 0.5,
        "mem_limit": "16G",
        "mem_guarantee": "0.5G",
    },
    "medium": {
        "cpu_limit": 2,
        "cpu_guarantee": 0.5,
        "mem_limit": "32G",
        "mem_guarantee": "0.5G",
    },
    "large": {
        "cpu_limit": 12,
        "cpu_guarantee": 1,
        "mem_limit": "64G",
        "mem_guarantee": "1G",
    },
    "extra_large": {
        "cpu_limit": 24,
        "cpu_guarantee": 1,
        "mem_limit": "192G",
        "mem_guarantee": "1G",
    },
}
```

**Fama.** Older compute server that is used primarily for teaching (theses, seminars, ...). 

Image options: 
```json
{
    "data_science": {
        "display_name": "Data Science Environment",
        "description": "For CPU-based data science jobs. Based on jupyter/datascience-notebook:92ce0af9989f docker image.",
        "kubespawner_override": {
            "image": "jupyter/datascience-notebook:92ce0af9989f",
        },
    },
}
```

Resource options:
```json
{
    "small": {
        "cpu_limit": 1,
        "cpu_guarantee": 0.5,
        "mem_limit": "12G",
        "mem_guarantee": "0.5G",
    },
    "medium": {
        "cpu_limit": 2,
        "cpu_guarantee": 0.5,
        "mem_limit": "24G",
        "mem_guarantee": "0.5G",
    },
}
```



## Contact

The e-Finance server landscape is administrated by Tino Cestonaro and Jonas De Paolis. Please feel free to contact us via e-mail. 

[Tino Cestonaro](mailto:cestonaro@wiwi.uni-frankfurt.de?subject=[GitHub]%20server-user%20repository)

[Florian Ewald](mailto:ewald@wiwi.uni-frankfurt.de?subject=[GitHub]%20server-user%20repository)


