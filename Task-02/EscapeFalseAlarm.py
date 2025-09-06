t = int(input())

for _ in range(t):
    n, x = map(int, input().split())
    doors = list(map(int, input().split()))

    button_used = False
    time_left = 0
    possible = True

    for state in doors:
        if state == 0:
            if time_left > 0:
                time_left -= 1
        else: 
            if not button_used:
                button_used = True
                time_left = x - 1  
            elif time_left > 0:
                time_left -= 1
            else:
                possible = False
                break

    print("YES" if possible else "NO")
