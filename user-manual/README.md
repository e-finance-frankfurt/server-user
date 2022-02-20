# user-manual

## 1&nbsp; Jupyter Hub

In this chapter, we will briefly describe how to navigate the hub control panel. 

<br />

![1_1_login.gif](_files/1_1_login.gif)

### 1.1&nbsp; Logging in

> Please make your first **login** as soon as possible, given that you yourself will need to set your password. Neither will you be provided with an initial password, nor will you be able to change an already set password later on - whatever string you type in during your first login will remain your password!

If you have been invited to use our compute servers, you have also been provided with `<user-name>` and `<ip-address>`. Using these credentials, you will be able to log in to the jupyter **hub** (hub control panel). 

To log in to the jupyter hub, ...

1. Enter http://`<ip-adress>` in your browser to access the JupyterHub login page. Note that this page can only be accessed from within the university network or via a virtual private network (VPN).
2. Enter your `<user-name>`. The user name is determined by the admin.
3. Enter an arbitrary password, which is entirely up to you. Only after your first login, your account will have password protection.
4. Click on the `sign in` button, leading you directly to the server options page for your default server.
5. Click on the `home` tab, leading you to the hub control panel.

<br />

![1_2_server.gif](_files/1_2_server.gif)

### 1.2&nbsp; Starting a Jupyter Server

> Having started a jupyter server, you will be able to use multiple Python (R, Julia, ...) **kernels** to run multiple programs at the same time, please understand that you do *not* need multiple jupyter servers! While we allow that you set up a second jupyter server (named server), please also understand that this will not help you lift resource limits as those are defined on a per-user basis. Use named servers *only* as a means to better organize your code base! 

Having logged in, you will be able to start a jupyter **server** (user instance), either your *default server* or a *named server*. 

To start your **default server**, ...

1. Click on the `home` tab.
2. Click on `start my server`, leading you to the server options page.
3. Select an environment (see chapter 1.3).
4. Click on the `start` button.

To create and start an additional **named server** ...

1. Click on the `home` tab.
2. Enter a name into the field `name your server` and click `add new server`, leading you to the server options page.
3. Select an environment (see chapter 1.3).
4. Click on the `start` button.

<br />

![1_3_environment.gif](_files/1_3_environment.gif)

### 1.3&nbsp; Selecting an Environment

> Note that user names with `stud_` prefix will *not* have access to the GPU-enabled image option(s) `[deep_learning]` as well as the larger resource options(s) `[large, extra_large]`. Students that *do* require access to those resources are assigned a user name *without* `stud_` prefix. 

Depending on your user name, the JupyterHub will give you different configuration options to choose from. Remember to choose your environment as small as possible (as large as necessary). 



## 2&nbsp; Jupyter Server

In this chapter, we will briefly describe all of the building blocks that make up your Jupyter Server environment. 

### 2.1&nbsp; User Interface Options

You are provided with two user interface options, Jupyter Lab and Jupyter Notebook. 

#### 2.1.1&nbsp; Jupyter Lab (default)

![2_1_lab.png](media/2_1_lab.png)

The default user interface for the jupyter server is the [Jupyter Lab](https://jupyterlab.readthedocs.io/en/latest/), the url being `http://<ip-adress>/user/<user-name>/lab`. 

The Jupyter Lab user interface gives you all functionality that you could possible need in one single browser tab. On the left-hand side, you can find `file browser`, `running kernels`, `table of contents` (for an open notebook), and the `extension manager`. On the right-hand side, you can find `property inspector` and the `debugging tool`. We may use the `kernel` tab to interrupt, shut down, or restart the selected kernel, meaning the kernel that is underlying the notebook or console that you are currently interacting with. We may use the `file` tab to log out, or to go back to the Jupyter Hub (hub control panel) from where we can start and stop all of our Jupyter Server instances. 

The Jupyter Lab user inteface allows for different ways of running your code. Both `notebook` and `console` can be used for interactive programming, use the `notebook` runtime if you want to extend your code with markdown (see chapter 3.1.1). The `terminal` is less convenient, but it plays an important role when facing long-running jobs (see chapter 3.1.2). 

The Jupyter Lab user interface allows you to open and display a variety of text file formats (.py, .txt, .csv, .json, ...). This can be especially useful if you are trying to display a large .csv file that you would otherwise never be able to fit into memory. 

#### 2.1.2&nbsp; Jupyter Notebook

![2_2_notebook.png](media/2_2_notebook.png)

The alternative user interface for the jupyter server is the [Jupyter Notebook](https://jupyter-notebook.readthedocs.io/en/latest/), the url being `http://<ip-adress>/user/<user-name>/tree`. You can simply switch to this user interface by replacing `/lab` with `/tree`. Note, however, that this switch will not persist when reloading the page, and that we strongly advise you to use Jupyter Lab.  

The Jupyter Notebook user interface is much more light-weight. The `Files` tab allows you to browse, upload, create, and delete files (including notebooks). The `Running` tab allows you to monitor and shutdown running notebooks and terminals. 

### 2.2&nbsp; Kernel options

You are provided with one or more kernel options, the default being Python. Please understand that, in terms of maintenance, we will not guarantee other options besides Python. 

#### 2.2.1&nbsp; Python

With all image options, you will have access to a Python 3.x kernel. Therefore, when working on your Jupyter Server, you will mainly use Python. (...)

#### 2.2.2&nbsp; Other

With some image options (`data_science`, ...), you will also have access to other types of kernels such as [R](https://www.r-project.org/about.html) or [Julia](https://julialang.org/). (...)

### 2.3&nbsp; Resource options

> While lots of resources are cool (we think so, too), please understand that you should take only as much as you can *actually* utilize (as much as you will *actually* need) in order to avoid overhead in resource consumption. 

Underlying your Jupyter Server are powerful computing resources that are shared among all user instances. In this regard, learning how to optimize your code is paramount (see chapter 4).

#### 2.3.1&nbsp; CPU

A typical Python program is single-threaded, that is, it uses only *half* of a single central processing unit (CPU) core. Consequently, chances are you may not even require multiple CPU cores. 

In a data-driven setting, however, a multi-threaded Python program will significantly speed up your workflow.  

#### 2.3.2&nbsp; GPU

A graphics processing unit (GPU) can be used for massively parallelized tasks, including (but not limited to) deep learning. 

#### 2.3.3&nbsp; RAM

On the one hand, CPU and GPU implement high-bandwith yet low-capacity memory, allowing for *extremely* fast data access (TB/s range) at the cost of size (MB range). On the other hand, solid state drive (SSD) and hard disk drive (HDD) represent high-capacity yet low-bandwith memory, allowing for large data storage (terabyte range) at the cost of speed (MB/s range). 

In the middle of this tiered formation, random access memory (RAM) is the sweet-spot in this trade-off. With regard to runtime, efficient memory utilization is one of the most important, if not *the* most important prerequisite to writing a fast program.  

### 2.4&nbsp; Storage options

You are provided with three storage options. 

#### 2.4.1&nbsp; User storage

Most of the time, you should use your 100 GB of user storage (internal storage). This is **both the fastest and the safest option**, as user storage is based on an NVMe SSD and can be accessed only by you and the admin. 

#### 2.4.2&nbsp; Temp storage

> To keep this drive empty, delete your files on a regular basis. To keep your files safe, always keep a back-up somewhere else. 

(optional) In some cases, you may want to *temporarily* share data with other users. The `temp` storage is relatively fast as it is based on a regular SSD, but please understand that *every* user has read and write permission for this drive and could therefore easily wipe out all of your data. 

#### 2.4.3&nbsp; Read-only storage

> While every user has to sign an non-disclosure agreement (NDA), refer to the [server-data](...) repository to see whether you may use a particular dataset from this drive. 

(optional) Usually, you will want to work with some kind of market data. The `read_only` storage is read-only, meaning that you may always read from this drive, but you do *not* have write permission (do *not* try to delete data). 

#### 2.4.4&nbsp; Databases

TODO: replace the read-only storage with a NoSQL databases. 



## 3&nbsp; Workflow

> Note that any changes made to the environment will not persist after a restart, given that it is rebuilt every time from a docker image. The data in your user storage, however, *will* persist. 

Here, we describe a typical workflow for Python. 

### 3.1&nbsp; Runtime options

Ultimately, you have two runtime options, notebook/console (prototyping) and terminal (production). 

#### 3.1.1&nbsp; Prototyping jobs via notebook or console

- write code cell-by-cell
- good for exploration
- 

#### 3.1.2&nbsp; Production jobs via terminal

- requires that you prepare script

... prevent culling
... describe behavior before shutdown
... always write to file

### 3.2&nbsp; Organization options

#### 3.2.1&nbsp; Scripting

#### 3.2.2&nbsp; Modules

### 3.3&nbsp; Important steps

#### 3.3.1&nbsp; **Request resources** <--- lieber separaten Punkt draus machen

#### 3.3.2&nbsp; Import modules

#### 3.3.3&nbsp; Load input data
... see also 4.1 I/O

#### 3.3.4&nbsp; Perform computations
... refer to 4.2 Compute

#### 3.3.5&nbsp; Monitor computations

#### 3.3.6&nbsp; Save output data
... results



## 4&nbsp; Optimized Python

### 4.1&nbsp; I/O

use datatable settings to prevent using all threads!

#### 4.1.1&nbsp; Reading data

... datatable
`dt.fread().to_pandas()`
dt.iread()

#### 4.1.2&nbsp; Writing
`dt.Frame(df).to_csv(path, compression="gzip")`


### 4.2&nbsp; Compute

#### 4.1.1&nbsp; Naïve approach via multiple kernels

#### 4.1.2&nbsp; Multi-threading and multi-processing

#### 4.1.3&nbsp; GPU-enabled Python


### 4.3&nbsp; Memory

#### 4.3.1&nbsp; Generator for larger-than-memory data



## 5&nbsp; Where to go from here?






