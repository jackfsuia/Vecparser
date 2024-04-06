# Vecparser
a parser that vectorizes your nested for-loops (in MATLAB, CVX) as much as possible. This technique is based on my post at https://ask.cvxr.com/t/how-to-vectorize-most-constraint-loops-in-cvx/9804 

## Quick Start
Run
```bash
git clone https://github.com/jackfsuia/Vecparser.git
```
Then install the requirements, run
```bash
pip install sly
```
To vectorize your for-loops from Matlab and CVX, write your loop to the loop_eiditor.m, then run
```bash
python vecparser.py
```
That's all! The results will be printed in loop_eiditor.m too, please refresh it.

## Example

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

This repo uses the matlablexer from [pymatlabparser](https://github.com/jol-jol/pymatlabparser). This repo's pymatlabparser folder is entirely copied from there with nearly zero modifiacations. Thanks for their wonderful works.
