T=int(input())
for i in range(T):
    X,Y=map(int,input().split())
    i=(X-1)//10+1
    j=(Y-1)//10+1
    print(abs(i-j))
