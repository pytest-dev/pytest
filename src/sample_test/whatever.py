'''
watever is a function that takes in euqal length lists
x and y, sort them, and then compares each element. 
if element in position i of list x is less than that of y, 
insert (x*y) into a new list, otherwise insert (y+3).
finally, print("whatever")
the function returns a new lst z
'''
def whatever_ok(x, y):
    
    x.sort()

    y.sort()

    z = []

    for i in range(len(x)):
        
        temp_x = x[i]

        temp_y = y[i]

        temp_difference = temp_x - temp_y

        if temp_difference < 0:

            temp_z = temp_x * temp_y

            z.append(temp_z)

        else:

            temp_3 = 3

            insert_to_z = temp_3 + temp_y

            z.append(insert_to_z)

    print("whatever")

    return z

def main():
    
    x = [30, 15, 1]

    y = [5, 10, 20]

    z = whatever(x,y)

    print(z)

if __name__ == "__main__":
    
    main()






