n = int(input())
while n > 0:
    z = int(input())
    x = input().split(" ")
    new = ["0"] * z
    new[0] = int(x[0])
    count = 0
    for i in range(0, z, 2):
        new[i] = x[count]
        count += 1
    count = z - 1
    for i in range(1, z, 2):
        new[i] = x[count]
        count -= 1
    print(" ".join(new))
    n -= 1
