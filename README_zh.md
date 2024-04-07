<p align="center">
    <img src="images/logo.PNG" width="45%" >
</p>
<!-- # Vecparser -->

<div align="center">
  
[English]((README.md)) | 简体中文

</div>

Vecparser 是一个自动将任意层 for 循环（在 MATLAB、CVX 中）尽可能向量化的解析器，由此节省大量的程序运行时间。这项技术基于我在https://ask.cvxr.com/t/how-to-vectorize-most-constraint-loops-in-cvx/9804的原始发帖。

## 快速启动
先克隆仓库
```bash
git clone https://github.com/jackfsuia/Vecparser.git
```
然后运行下面命令安装依赖项，
```bash
pip install sly
```
要向量化你的 MATLAB 和 CVX 中的 for 循环，请先将循环写到 [loop_eiditor.m](loop_eiditor.m)，在此之前建议读一下[注意事项](#注意事项))。 然后运行
```bash
python vecparser.py
```
大功告成! 向量化后的表达式也会打印在 [loop_eiditor.m](loop_eiditor.m) , 所以请刷新一下这个文件。

## 示例
比如下面的原始循环，先把它抄到[loop_eiditor.m](loop_eiditor.m)如下:
```matlab
% loop_eiditor.m
for n1=1:N1
    for n2=1:N2
        for n3=1:N3
            for n4=1:N4
                if n1~=n2*n3 && n3>n4^3
                    x(n1,n2,n3,n4)= (y(n1,n3)+z(n4))*h(n2,n3,n1); % note: size(z) has to be "N4 1", not "1 N4".
                    q(n4,n3,n2,n1)= -h(n2,n3,n1)+((y(n1,n3)+z(n4))*h(n2,n3,n1))^2;
                end
            end
        end
    end
end
```
然后运行下面命令 
```bash
python vecparser.py
```
结果就会附加到 [loop_eiditor.m](loop_eiditor.m) 后面，如下
```matlab
% loop_eiditor.m
for n1=1:N1
    for n2=1:N2
        for n3=1:N3
            for n4=1:N4
                if n1~=n2*n3 && n3>n4^3
                    x(n1,n2,n3,n4)= (y(n1,n3)+z(n4))*h(n2,n3,n1); % note: size(z) has to be "N4 1", not "1 N4".
                    q(n4,n3,n2,n1)= -h(n2,n3,n1)+((y(n1,n3)+z(n4))*h(n2,n3,n1))^2;
                end
            end
        end
    end
end

%-------------------------vectorized by Vecparser as-----------------------

cached_condition_for_this=(permute(repmat(repmat((1:N1)',1,N2,N3)~=permute(repmat(repmat((1:N2)',1,N3).*permute(repmat((1:N3)',1,N2),[2,1]),1,1,N1),[3,1,2]),1,1,1,N4),[2,3,1,4])&permute(repmat(permute(repmat((1:N3)',1,N4),[2,1])>repmat((1:N4)'.^3,1,N3),1,1,N2,N1),[3,2,4,1]));

x=permute(permute((cached_condition_for_this),[4,1,2,3]).*permute((permute(repmat((permute(repmat(y,1,1,N4),[1,3,2])+permute(repmat(z,1,N1,N3),[2,1,3])),1,1,1,N2),[4,3,1,2]).*repmat(h,1,1,1,N4)),[4,1,2,3])+permute((1-permute((cached_condition_for_this),[3,4,1,2])),[2,3,4,1]).*permute(x,[4,2,3,1]),[4,2,3,1]);

q=permute(permute((cached_condition_for_this),[4,1,2,3]).*permute((repmat(-h,1,1,1,N4)+permute(permute((permute(repmat((permute(repmat(y,1,1,N4),[1,3,2])+permute(repmat(z,1,N1,N3),[2,1,3])),1,1,1,N2),[4,3,1,2]).*repmat(h,1,1,1,N4)),[3,4,1,2]).^2,[3,4,1,2])),[4,1,2,3])+permute((1-permute((cached_condition_for_this),[3,4,1,2])),[2,3,4,1]).*permute(q,[1,3,2,4]),[1,3,2,4]);

%-----Please clear this file each time before you write a new loop on------
```
Now copy the results to your matlab to replace the loops, and try them out.

 *Does this help you save some run time? Give us a :star:*
 
## 注意事项
**这是个实验性的项目，现阶段有很多bug. 现在仅支持单个 if 块或者单个非if块**. 例如，下面的例子有一个if 块加上一个非if 块，是不支持的:
```matlab
for n1=1:N1
    for n2=1:N2
        for n3=1:N3
            for n4=1:N4

                % if块起始
                if n1~=n2*n3 && n3>n4^3
                    x(n1,n2,n3,n4)= (y(n1,n3)+z(n4))*h(n2,n3,n1);
                end
                % if块结束

                % 非if块起始
                q(n4,n3,n2,n1)= -h(n2,n3,n1)+((y(n1,n3)+z(n4))*h(n2,n3,n1))^2; % 注意: size(z) has to be "N4 1", not "1 N4".
                 % 非if块结束
            end
        end
    end
end
```
但下面的只有一个非if块的循环是支持的:

```matlab
for n1=1:N1
    for n2=1:N2
        for n3=1:N3
            for n4=1:N4
                % 非if块起始
                x(n1,n2,n3,n4)= (y(n1,n3)+z(n4))*h(n2,n3,n1);
                q(n4,n3,n2,n1)= -h(n2,n3,n1)+((y(n1,n3)+z(n4))*h(n2,n3,n1))^2; % note: size(z) has to be "N4 1", not "1 N4".
                % 非if块结束
            end
        end
    end
end
```
## Future Work
- Support multiple blocks of if-else in one loop. This may be soon.
- Support reduce operators like `sum`, `norm`, `*`(matrix multiplication).
- Explore its use on other languages (e.g., python)
  
## License

ShampooSalesAgent is licensed under the Apache 2.0 License found in the [LICENSE](LICENSE) file in the root directory of this repository.

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
