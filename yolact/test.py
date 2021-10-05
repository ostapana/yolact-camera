position = int(input())
finish = int(input())
wall_1 = int(input())
wall_2 = int(input())

while position != finish:
    if position + 1  == wall_1 or position + 1 == wall_2:
        print('прыжок')
        position += 2
    else:
        print('шаг')
        position += 1