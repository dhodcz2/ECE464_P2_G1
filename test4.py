from time import time
x = {n for n in range(0, 10000)}
y = [n for n in range(0, 10000)]

begin = time()
for n in x:
    pass
print(time() - begin)

begin = time()
for n in y:
    pass
print(time() - begin)

z = {'a': 1}
begin = time()
for _ in range(0, 10000):
    z.get('a')
print(time() - begin)

begin = time()
for _ in range(0, 10000):
    z['a']
print(time() - begin)
