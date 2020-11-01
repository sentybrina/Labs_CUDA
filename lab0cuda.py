# -*- coding: utf-8 -*-
"""Lab0CUDA.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1R88_EZwPKA-ElJd9RKcv22Vfipid0mva
"""

# Commented out IPython magic to ensure Python compatibility.
import numpy as np
from numba import cuda
from time import time
import math
import matplotlib.pyplot as plt
# %matplotlib inline

def get_matrix(n):
  a = np.random.randint(0, 10, (n, n)).astype(np.float64)
  b = np.random.randint(0, 10, (n, n)).astype(np.float64)
  c = np.zeros((n, n)).astype(np.float64)
  return a, b, c

# обычное умножение поэлементное - берет две матрицы, возвразает итоговую матрицу и время работы
def mul_cpu(a, b):
  n=len(a)
  c = np.zeros((n,n))
  start = time()
  for i in range(n):
    for j in range(n):
      for k in range(n):
        c[i, j] += a[i,k] * b[k,j]
  return c, time()-start
    
# умножение с помощю встроенного алгоритма, возвращает итоговую матрицу и время работы
def mul_cpu_numpy(a, b):
  start = time()
  c = np.dot(a, b)
  return c, time() - start

# функция вычисления одного элемента, дается установка компилятору задействовать куду
@cuda.jit
def gpu_mul_operation(a, b, c):
    i, j = cuda.grid(2)
    if i < c.shape[0] and j < c.shape[1]:
      tmp = 0
      for k in range(a.shape[1]):
        tmp += a[i, k] * b[k, j]
      c[i, j] = tmp

# функция которая, подготавливает все для запуска на гпу и вызывает функцию
def prepare_and_exec_gpu_mul(a, b, c, n):
  # количество нитей в блоке
  tread_number_block = 32
  # копируем на гпу все данные
  a_global = cuda.to_device(a)
  b_global = cuda.to_device(b)
  c_global = cuda.device_array((n, n))
    
  # создаем сетку
  threadsperblock = (tread_number_block, tread_number_block)
  blockspergrid_x = int(math.ceil(a.shape[0] / threadsperblock[1]))
  blockspergrid_y = int(math.ceil(b.shape[1] / threadsperblock[0]))
  blockspergrid = (blockspergrid_x, blockspergrid_y)

  start = time()
  # вызываем функцию на сетке
  gpu_mul_operation[blockspergrid, threadsperblock](a_global, b_global, c_global)
  gpu_time = time() - start
  c_gpu = c_global.copy_to_host() 
  return c_gpu, gpu_time

# функция замера времени на матрицах размерности n - вычисления производятся count раз, затем усредняются
def expiriens(n, count):  
  gpu_time_sum = 0
  cpu_time_sum = 0
  for _ in range(count):
    a, b, c = get_matrix(n)
    c_gpu, gpu_time = prepare_and_exec_gpu_mul(a, b, c, n)
    gpu_time_sum+=gpu_time
    c_cpu, cpu_time = mul_cpu(a, b)
    cpu_time_sum+=cpu_time

  print('Размерность матрицы', n)
  print('Усредненное время умножения на CPU:',cpu_time/count)
  print('Усредненное время умножения на GPU:',gpu_time/count)
  print('Ускорение',cpu_time/gpu_time )
  return cpu_time/gpu_time

# функция проверки корректности функций подсчета на матрице размерности n
def functions_are_correct(n):
  a, b, c = get_matrix(n)
  c_numpy = mul_cpu_numpy(a,b)[0]
  c_cpu = mul_cpu(a,b)[0]
  c_gpu = prepare_and_exec_gpu_mul(a, b, c, n)[0]
  if np.array_equal(c_numpy, c_cpu):
    print('CPU считает корректно')
  if np.array_equal(c_numpy, c_gpu):
    print('GPU считает корректно')

functions_are_correct(128)
count = 1
n_array = [128, 256, 512, 1024, 2048]
time_array = [expiriens(n_array_i, count) for n_array_i in n_array]

plt.plot(np.array(n_array), np.array(time_array)) 
plt.xlabel('Размерность')
plt.ylabel('Ускорение')
plt.show()