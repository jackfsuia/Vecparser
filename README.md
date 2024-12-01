## loop-killer

English | [简体中文](README_zh.md)
</div>
<!-- # Vecparser -->
A parser that auto vectorizes your nested for-loops (in MATLAB, CVX) as much as possible, which is to save tons of run time (97% in some cases). This technique is based on my original post at https://ask.cvxr.com/t/how-to-vectorize-most-constraint-loops-in-cvx/9804 in 2022.

Here is the [performance](#performance):

<p align="center"><img src="images/loop.png" width="60%" ></p>

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Quick Start](#quick-start)
- [Example](#example)
  - [a Matlab example](#a-matlab-example)
  - [a CVX example](#a-cvx-example)
- [Performance](#performance)
- [Notice](#notice)
- [Future Work](#future-work)
- [License](#license)
- [Citation](#citation)
- [Acknowledgement](#acknowledgement)
## Quick Start
Run
```bash
git clone https://github.com/jackfsuia/loop-killer.git && cd loop-killer
```
Then install the requirements, run
```bash
pip install sly
```
To vectorize your for-loops from Matlab and CVX, write your loop (please first read the [Notice](#Notice)) to the [loop_eiditor.m](loop_eiditor.m), then run
```bash
python vecparser.py
```
That's all! The results will be printed in [loop_eiditor.m](loop_editor.m) too, please refresh it.

## Example
### a Matlab example
To vectorize the Matlab loops, copy the loops you want to vectorize to [loop_eiditor.m](loop_editor.m), like this one:
```matlab
% loop_eiditor.m
for n1=1:N1
    for n2=1:N2
        x(n1,n2)= -(y(n1)+z(n2))*m(n2,n1);
        if n1>n2*2
            for n3=1:N3
                for n4=1:N4
                    if n1~=n2*n3 && n3>n4^3
                        q(n4,n3,n2,n1)= -h(n2,n3,n1)+((n(n1,n3)+w(n4))*t(n2,n3,n1))^2;
                    end
                    u(n1,n2,n3,n4)= (p(n1,n3)+a(n4))*b(n2,n3,n1);
                end
            end
        end
    end
end
```
then run 
```bash
python vecparser.py
```
The result will be appended to [loop_eiditor.m](loop_eiditor.m) as
```matlab
% loop_eiditor.m
for n1=1:N1
    for n2=1:N2
        x(n1,n2)= -(y(n1)+z(n2))*m(n2,n1);
        if n1>n2*2
            for n3=1:N3
                for n4=1:N4
                    if n1~=n2*n3 && n3>n4^3
                        q(n4,n3,n2,n1)= -h(n2,n3,n1)+((n(n1,n3)+w(n4))*t(n2,n3,n1))^2;
                    end
                    u(n1,n2,n3,n4)= (p(n1,n3)+a(n4))*b(n2,n3,n1);
                end
            end
        end
    end
end

%-------------------------vectorized by Vecparser as-----------------------

x=-(repmat(y,1,N2)+permute(repmat(z,1,N1),[2,1])).*permute(m,[2,1]);

cached_condition_for_this=((repmat((1:N1)',1,N2)>permute(repmat((1:N2)'.*2,1,N1),[2,1])));

cached_condition_for_this=(repmat((repmat((1:N1)',1,N2)>permute(repmat((1:N2)'.*2,1,N1),[2,1])),1,1,N3,N4)&permute((permute(repmat(repmat((1:N1)',1,N3,N2)~=permute(repmat(permute(repmat((1:N2)',1,N3),[2,1]).*repmat((1:N3)',1,N2),1,1,N1),[3,1,2]),1,1,1,N4),[1,4,3,2])&permute(repmat(repmat((1:N3)',1,N4)>permute(repmat((1:N4)'.^3,1,N3),[2,1]),1,1,N1,N2),[3,2,4,1])),[1,3,4,2]));

q=permute(permute(permute((cached_condition_for_this),[1,4,2,3]).*(permute(repmat(-h,1,1,1,N4),[3,4,1,2])+(permute(repmat((repmat(n,1,1,N4)+permute(repmat(w,1,N1,N3),[2,3,1])),1,1,1,N2),[1,3,4,2]).*permute(repmat(t,1,1,1,N4),[3,4,1,2])).^2),[1,3,4,2])+permute(permute((1-permute((cached_condition_for_this),[1,3,4,2])),[1,3,4,2]).*permute(q,[4,1,3,2]),[1,3,4,2]),[4,3,2,1]);

cached_condition_for_this=((repmat((1:N1)',1,N2)>permute(repmat((1:N2)'.*2,1,N1),[2,1])));

u=permute(permute(repmat((cached_condition_for_this),1,1,N3,N4).*permute((permute(repmat((repmat(p,1,1,N4)+permute(repmat(a,1,N1,N3),[2,3,1])),1,1,1,N2),[1,3,4,2]).*permute(repmat(b,1,1,1,N4),[3,4,1,2])),[1,3,4,2]),[1,4,2,3])+permute((1-permute((cached_condition_for_this),[1,3,4,2])),[1,3,4,2]).*permute(u,[1,4,2,3]),[1,3,4,2]);

%-----Please clear this file each time before you write a new loop on------
```
Now copy the results to your matlab to replace the loops, and try them out.

### a CVX example
It goes the same ways as Matlab, except all terms will be automatically moved to right side of inqualities for efficiency. So what you get will be like:
```matlab
for n1=1:N1
    for n2=1:N2
        for n3=1:N3
            if n1~=n2*n3 && n3>n2^3
                x(n1) >= y(n2) + z(n2, n3);
            end
        end
    end
end

%-------------------------vectorized by Vecparser as-----------------------

cached_condition_for_this=((repmat((1:N1)',1,N3,N2)~=permute(repmat(permute(repmat((1:N2)',1,N3),[2,1]).*repmat((1:N3)',1,N2),1,1,N1),[3,1,2])&permute(repmat(repmat((1:N3)',1,N2)>permute(repmat((1:N2)'.^3,1,N3),[2,1]),1,1,N1),[3,1,2])));

0>=(repmat(-(x),1,N3,N2)+permute(repmat((permute(repmat(y,1,N3),[2,1])+permute(z,[2,1])),1,1,N1),[3,1,2])).*(cached_condition_for_this);

%-----Please clear this file each time before you write a new loop on------
```



## Performance
I ran this performance test on my old computer: Intel(R) Xeon(R) CPU E5-2660 v2 @ 2.20GHz, RAM 16G. Here is what I got:
![performance](images/loop.png)

It was observed that **when the loop of iterations is too big, vectorization of it might cause my computer to crash due to memory shortage,** therefore it ran slower than traditional loops in those extreme cases. It will be meaningful to see the trade off provided limited RAM, and how it'll perform when GPU come into play.

## Notice
Now it supports nested 'if' and non-if blocks anywhere in loop, but **don't support 'else'**, so please change it to 'if' instead. Support all the native element-wise operators: +, -, *, /, and so on. Natively support self-defined vectorized dimension-invariant functions. Support CVX style convex inequality like '>=','<=','=='. **It might have bugs, for being a experimental project.**

## Future Work
- Support reduce operators like `sum`, `norm`, `*`(matrix multiplication).
- Explore its use on other languages (e.g., python)
  
## License

Vecparser is licensed under the Apache 2.0 License found in the [LICENSE](LICENSE) file in the root directory of this repository.

## Citation

If this work is helpful, please kindly cite as:

```bibtex
@article{Vecparser,
  title={Vecparser: a parser that vectorizes your nested for-loops (in MATLAB, CVX) as much as possible.}, 
  author={Yannan Luo},
  year={2024},
  url={https://github.com/jackfsuia/Vecparser}
}
```
## Acknowledgement

This repo uses the matlablexer from [pymatlabparser](https://github.com/jol-jol/pymatlabparser). This repo's [pymatlabparser](pymatlabparser) folder is entirely copied from there with nearly zero modifiacations. Thanks for their wonderful works.
