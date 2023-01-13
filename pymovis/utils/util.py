import torch
import numpy as np
import random

from functools import partial
import multiprocessing as mp

def seed(x=777):
    torch.manual_seed(x)
    torch.cuda.manual_seed(x)
    torch.cuda.manual_seed_all(x)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    np.random.seed(x)
    random.seed(x)

def run_parallel(func, iterable, num_cpus=mp.cpu_count(), desc="Running parallel ...", **kwargs):
    print(desc, f"[{num_cpus} CPUs]")

    func_with_kwargs = partial(func, **kwargs)
    with mp.Pool(num_cpus) as pool:
        res = pool.map(func_with_kwargs, iterable)

    return res