# user-manual



## 1 Jupyter Hub

### 1.1 Login

### 1.2 Starting a Jupyter Server

... also named servers

### 1.3 Selecting an Environment



## 2 Jupyter Server

### 2.1 User Interface Options

#### 2.1.1 Jupyter Lab (default)
... include image
... default

#### 2.1.2 Jupyter Notebook
... include image

### 2.2 Kernel options

#### 2.2.1 Python
#### 2.2.2 R

### 2.3 Storage options

#### 4.2.1 `read_only`
#### 4.2.2 `temp`



## 3 Workflow

Here, we describe steps for Python. 

### 3.1 Runtime options

### 3.1.1 Prototyping via notebook

### 3.1.2 Long-running jobs via terminal

... prevent culling
... describe behavior before shutdown
... always write to file

### 3.2 Organization options

#### 3.2.1 Scripting

#### 3.2.2 Modules

### 3.3 Important steps

#### 3.3.1 **Request resources** <--- lieber separaten Punkt draus machen

#### 3.3.2 Import modules

#### 3.3.3 Load input data
... see also 4.1 I/O

#### 3.3.4 Perform computations
... refer to 4.2 Compute

#### 3.3.5 Monitor computations

#### 3.3.5 Save output data
... results



## 4 Optimized Python

### 4.1 I/O

use datatable settings to prevent using all threads!

#### 4.1.1 Reading data

... datatable
`dt.fread().to_pandas()`
dt.iread()

#### 4.1.2 Writing
`dt.Frame(df).to_csv(path, compression="gzip")`


### 4.2 Compute

#### 4.1.1 Naïve approach via multiple kernels

#### 4.1.2 Multi-threading and multi-processing

#### 4.1.3 GPU-enabled Python


### 4.3 Memory

#### 4.3.1 Generator for larger-than-memory data



## 5 Where to go from here?






