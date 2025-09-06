t = int(input())

for i in range(t):
    n = int(input())
    c = list(map(int, input().split()))  
    j= {}
    for o in c:
        j[o] = j.get(o, 0) + 1
    m = max(j.values())
    print(n - m)
