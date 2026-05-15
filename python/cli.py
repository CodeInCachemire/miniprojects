import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument('greeting', help = 'The greeting message!')
#numbers provided are floats
#number of args are 2
#help text
parser.add_argument('-n', '--numbers', type=float, nargs= 2, help = 'Add two floats, give floats!')
parser.add_argument('-v', '--verbose', type=int, choices = [0, 1, 2], help = 'Determines how much info is displayed')
parser.add_argument('-f', '--file', type = str, help = 'Write to file')
parser.add_argument('--debug', action = "store_true", help = "Enables true or false.")

args = parser.parse_args()

print(args)
print(args.numbers)

if args.verbose is None: 
    print(args.greeting)
    if args.numbers is not None: 
        print(f"Here is for nothing {sum(args.numbers)}")
else:
    if args.verbose >= 0:
        print(args.greeting)
        if args.numbers is not None:
            print(f"Here for 0, {sum(args.numbers)}")
        if args.verbose >=1:
            print(f"Here for 1{args.numbers}")
        if args.verbose ==2:
            print("Extra info for 2")
