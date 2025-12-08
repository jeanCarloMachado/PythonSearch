
# PythonSearch Design


Python search core is designed to run fully on the local machine.


```mermaid
graph LR
    A[User] -- starts python search and interacts with --> B[FZF in kitty]
    B --> C[PythonSearch entries ranked]
```
